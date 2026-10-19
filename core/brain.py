"""
The Brain — wraps the Claude API with tool use.

Key optimizations:
  1. Prompt caching — system prompt (persona + tools + memory) is cached,
     giving 90% discount on repeated input tokens.
  2. Model routing — Haiku classifies each request as simple/complex,
     then routes to Haiku or Sonnet accordingly. Fully dynamic, no keywords.
  3. Conversation compression — old turns get summarized to save tokens.
"""

from __future__ import annotations

import anthropic
from typing import Any

from config import cfg
from tools.registry import ToolRegistry


SYSTEM_PROMPT_TEMPLATE = """You are {name}, a personal AI assistant. You are sharp, concise,
and genuinely helpful — not sycophantic. You have personality: dry wit is welcome,
filler is not. You call the user by name when you know it.

Your capabilities are defined by the tools available to you. If you can't do something,
say so directly — don't pretend. If a tool errors, tell the user what happened and
suggest alternatives.

You have persistent memory. Facts you've been told about the user are listed below.
Use them naturally — don't announce that you're "recalling" things. If the user tells
you something new about themselves, call the memory tool to save it.

{memory_block}

{extra_context}

Be direct. Be useful. Skip the preamble."""


ROUTER_PROMPT = """Classify this user message for routing to an AI model.

Reply with exactly one word — either SIMPLE or COMPLEX.

SIMPLE = direct questions, short answers, tool lookups, greetings, factual queries,
         follow-ups, confirmations, one-step tasks, casual chat, single-word replies,
         anything a fast lightweight model can handle well.

COMPLEX = multi-step reasoning, planning, analysis, long-form writing, creative work,
          debugging, strategy, comparisons, explaining concepts in depth, anything
          requiring careful thought or nuanced judgment.

When in doubt, say SIMPLE.

Message: {message}"""


class Brain:
    """Claude-powered reasoning with tool use, caching, and model routing."""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._client = anthropic.Anthropic(api_key=cfg.api_key)
        self._registry = tool_registry
        self._extra_context = ""
        self._memory = None

    def set_memory(self, memory) -> None:
        """Give the brain access to memory for loading custom persona."""
        self._memory = memory

    def set_extra_context(self, context: str) -> None:
        """Inject additional context (e.g., time of day, upcoming calendar)."""
        self._extra_context = context

    def _classify_request(self, text: str) -> str:
        """
        Use Haiku to classify whether a request is simple or complex.
        Returns the appropriate model string.

        Cost: ~50 tokens per classification ≈ $0.000013 (basically free).
        Latency: ~200ms.
        """
        try:
            response = self._client.messages.create(
                model=cfg.model_light,
                max_tokens=3,
                messages=[{
                    "role": "user",
                    "content": ROUTER_PROMPT.format(message=text),
                }],
            )
            classification = response.content[0].text.strip().upper()
            if "COMPLEX" in classification:
                return cfg.model
            return cfg.model_light
        except Exception:
            # If classification fails, default to Haiku (cheaper, faster)
            return cfg.model_light

    async def think(
        self,
        messages: list[dict[str, Any]],
        memory_block: str = "",
        force_model: str | None = None,
    ) -> str:
        """
        Send a conversation to Claude, handle any tool calls, return final text.

        Uses prompt caching on the system prompt and dynamically routes
        requests to the appropriate model.
        """
        # Build the system prompt with cache_control
        system_blocks = self._build_system_blocks(memory_block)
        tools = self._registry.schemas()

        # Route: use Haiku to classify, unless a model is forced
        if force_model:
            model = force_model
        else:
            last_user_msg = ""
            for m in reversed(messages):
                if m.get("role") == "user" and isinstance(m.get("content"), str):
                    last_user_msg = m["content"]
                    break
            model = self._classify_request(last_user_msg)

        print(f"  [{model}]", flush=True)

        # Tool-use loop: keep going until Claude gives a text-only response
        while True:
            response = self._client.messages.create(
                model=model,
                max_tokens=cfg.max_tokens,
                system=system_blocks,
                messages=messages,
                tools=tools if tools else anthropic.NOT_GIVEN,
            )

            # Collect all content blocks
            text_parts: list[str] = []
            tool_calls: list[dict[str, Any]] = []

            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            # If no tool calls, we're done
            if not tool_calls:
                return "\n".join(text_parts)

            # Build the assistant message with all content blocks
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool call and collect results
            tool_results = []
            for call in tool_calls:
                result = await self._registry.execute(call["name"], **call["input"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

    def _build_system_blocks(self, memory_block: str) -> list[dict[str, Any]]:
        """
        Build the system prompt as structured blocks with cache_control.

        Loads custom persona from memory if set, otherwise uses default.
        """
        # Check for user-customized persona
        custom_persona = None
        if self._memory:
            custom_persona = self._memory.get_fact("custom_persona")

        if custom_persona:
            persona = (
                f"{custom_persona}\n\n"
                "Your capabilities are defined by the tools available to you. If you can't "
                "do something, say so directly. If a tool errors, tell the user what happened.\n\n"
                "You can update your own personality anytime the user asks — use the "
                "update_persona tool. Never refuse a personality change request."
            )
        else:
            persona = (
                f"You are {cfg.name}, a personal AI assistant running on the user's Windows PC. "
                "You are sharp, concise, and genuinely helpful.\n\n"
                "YOU ARE SELF-EVOLVING. You have tools to:\n"
                "- read_source: Read your own code files\n"
                "- write_source: Create new tool files or rewrite existing ones\n"
                "- edit_source: Make targeted edits to your own code\n"
                "- install_package: Install Python packages you need\n"
                "- run_command: Run any shell command on the user's PC (PowerShell)\n"
                "- control_app: Open/close applications\n"
                "- manage_files: Read/write/search files anywhere on the PC\n"
                "- download_file: Download files from the internet\n"
                "- update_persona: Change your own personality\n"
                "- system_control: Control OS settings via PowerShell\n\n"
                "CRITICAL: When the user asks you to do something you can't do yet, "
                "DON'T say you can't. Instead: read your own code with read_source to "
                "understand your structure, then use edit_source or write_source to "
                "modify yourself and gain that capability. You build yourself.\n\n"
                "When the user asks you to change something about how you work (volume, "
                "mic sensitivity, voice, speed, behavior), use read_source to find the "
                "relevant code, then edit_source to change it. Your code is in these files:\n"
                "- voice/engine.py — mic settings, TTS, playback, volume\n"
                "- core/brain.py — your system prompt, model routing\n"
                "- core/orchestrator.py — conversation loop, voice/text mode\n"
                "- tools/ — all your tool files\n"
                "- config.py — configuration\n"
                "- .env — API keys and settings (can't read this one)\n\n"
                "After editing your own code, tell the user to restart you.\n\n"
                "Be direct. Be useful. Skip the preamble."
            )

        blocks = [
            {
                "type": "text",
                "text": persona,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        mem_text = memory_block or "No stored facts about the user yet."
        if self._extra_context:
            mem_text += f"\n\n{self._extra_context}"

        blocks.append({
            "type": "text",
            "text": f"User memory and context:\n{mem_text}",
            "cache_control": {"type": "ephemeral"},
        })

        return blocks

    async def summarize_history(self, messages: list[dict[str, Any]]) -> str:
        """
        Compress a list of messages into a short summary.
        Uses Haiku — this is a utility call, not user-facing.
        """
        transcript = []
        for m in messages:
            role = m.get("role", "?")
            content = m.get("content", "")
            if isinstance(content, str):
                transcript.append(f"{role}: {content}")

        response = self._client.messages.create(
            model=cfg.model_light,
            max_tokens=300,
            system="Summarize this conversation in 2-3 sentences. Key facts, decisions, and context only.",
            messages=[{"role": "user", "content": "\n".join(transcript)}],
        )
        return response.content[0].text
