"""
The Orchestrator — Tadashi's main event loop.

Ties together: input → brain → tools → memory → output.
Supports both text and voice modes.
"""

from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

from config import cfg
from core.brain import Brain
from core.memory import Memory
from tools.registry import registry


# ── Local intent matching ──────────────────────────────────────────

_LOCAL_INTENTS: list[tuple[re.Pattern, Any]] = []


def _register_local(pattern: str):
    def decorator(func):
        _LOCAL_INTENTS.append((re.compile(pattern, re.IGNORECASE), func))
        return func
    return decorator


@_register_local(r"^(?:what(?:'s| is) the )?time\??$")
def _handle_time(_match) -> str:
    now = datetime.now(ZoneInfo("Asia/Singapore"))
    return now.strftime("It's %I:%M %p, %A %B %d.")


@_register_local(r"^(?:hi|hello|hey|yo|sup|what'?s up)\s*[!.?]*$")
def _handle_greeting(_match) -> str:
    hour = datetime.now(ZoneInfo("Asia/Singapore")).hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting}. What can I do for you?"


def _try_local_intent(text: str) -> str | None:
    stripped = text.strip()
    for pattern, handler in _LOCAL_INTENTS:
        match = pattern.match(stripped)
        if match:
            return handler(match)
    return None


# ── Orchestrator ───────────────────────────────────────────────────

class Orchestrator:
    HISTORY_COMPRESS_THRESHOLD = 20
    HISTORY_KEEP_RECENT = 6

    def __init__(self) -> None:
        self.memory = Memory(cfg.db_path)
        self.brain = Brain(registry)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
        self.messages: list[dict[str, Any]] = []
        self._compressed_context: str = ""

    async def start(self, voice_mode: bool = False) -> None:
        registry.auto_discover()

        from tools.memory_tool import set_memory
        from tools.persona_tool import set_memory as set_persona_memory
        set_memory(self.memory)
        set_persona_memory(self.memory)
        self.brain.set_memory(self.memory)

        mode_label = "Voice" if voice_mode else "Text"
        print(f"\n{'=' * 60}")
        print(f"  {cfg.name.upper()} — Online ({mode_label} Mode)")
        print(f"  Session: {self.session_id}")
        print(f"  Models: {cfg.model} (complex) / {cfg.model_light} (simple)")
        print(f"  Tools: {', '.join(registry.tool_names)}")
        print(f"{'=' * 60}\n")

        summaries = self.memory.get_recent_summaries(limit=3)
        if summaries:
            summary_text = "\n".join(f"- {s['summary']}" for s in summaries)
            self.brain.set_extra_context(
                f"Recent conversation summaries:\n{summary_text}"
            )

        if voice_mode:
            await self._voice_loop()
        else:
            await self._text_loop()

    async def _voice_loop(self) -> None:
        """Voice interaction loop — always listening, interruptible."""
        from voice.engine import VoiceEngine

        voice = VoiceEngine(cfg.tts_voice)
        voice.start_listening()
        await voice.speak(f"{cfg.name} online. How can I help?")

        print("  Always listening. Say 'goodbye' to end.\n")

        while True:
            try:
                # Wait for user input (background listener fills the queue)
                user_input = await voice.get_input()

                if user_input.lower().strip() in ("quit", "exit", "bye", "goodbye", "stop"):
                    await voice.speak("Session ended. See you next time.")
                    await self._end_session()
                    voice.cleanup()
                    break

                # Check if there's a newer input already (user kept talking)
                latest_input = user_input
                while True:
                    try:
                        newer = voice._input_queue.get_nowait()
                        latest_input = latest_input + " " + newer
                    except:
                        break

                response = await self.process(latest_input)
                print(f"\n  {cfg.name}: {response}\n")

                await voice.speak(response)

                # If interrupted mid-speech, the new input is already in the queue
                if voice.was_interrupted():
                    print("  [Interrupted — processing new input]", flush=True)

            except KeyboardInterrupt:
                voice.cleanup()
                break
            except Exception as e:
                print(f"  Error: {e}")
                continue

    async def _text_loop(self) -> None:
        print(f"  Type 'quit' or 'exit' to end the session.\n")

        while True:
            try:
                user_input = input(f"  You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye", "goodbye"):
                await self._end_session()
                break

            if user_input.startswith("/"):
                result = await self._handle_command(user_input)
                if result:
                    print(f"\n  {cfg.name}: {result}\n")
                continue

            response = await self.process(user_input)
            print(f"\n  {cfg.name}: {response}\n")

    async def process(self, user_input: str) -> str:
        local_response = _try_local_intent(user_input)
        if local_response is not None:
            self.memory.save_message(self.session_id, "user", user_input)
            self.memory.save_message(self.session_id, "assistant", local_response)
            return local_response

        self.memory.save_message(self.session_id, "user", user_input)
        self.messages.append({"role": "user", "content": user_input})

        await self._maybe_compress_history()

        api_messages = self._build_api_messages()
        memory_block = self.memory.facts_as_prompt_block()

        response = await self.brain.think(
            messages=api_messages,
            memory_block=memory_block,
        )

        self.memory.save_message(self.session_id, "assistant", response)
        self.messages.append({"role": "assistant", "content": response})

        return response

    def _build_api_messages(self) -> list[dict[str, Any]]:
        if not self._compressed_context:
            return self.messages.copy()

        context_msg = {
            "role": "user",
            "content": f"[Earlier in this conversation: {self._compressed_context}]",
        }
        assistant_ack = {
            "role": "assistant",
            "content": "Understood, I have that context.",
        }
        return [context_msg, assistant_ack] + self.messages.copy()

    async def _maybe_compress_history(self) -> None:
        if len(self.messages) < self.HISTORY_COMPRESS_THRESHOLD:
            return

        split_point = len(self.messages) - self.HISTORY_KEEP_RECENT
        old_messages = self.messages[:split_point]
        recent_messages = self.messages[split_point:]

        try:
            new_summary = await self.brain.summarize_history(old_messages)

            if self._compressed_context:
                self._compressed_context = f"{self._compressed_context} | {new_summary}"
            else:
                self._compressed_context = new_summary

            self.messages = recent_messages

        except Exception:
            self.messages = self.messages[-self.HISTORY_KEEP_RECENT:]

    async def _handle_command(self, command: str) -> str | None:
        cmd = command.lower().strip()

        if cmd == "/memory":
            facts = self.memory.get_all_facts()
            if not facts:
                return "No facts stored yet."
            lines = ["Stored memory:"]
            for f in facts:
                lines.append(f"  [{f.category}] {f.key}: {f.value}")
            return "\n".join(lines)

        elif cmd == "/clear":
            self.messages.clear()
            self._compressed_context = ""
            return "Conversation context cleared (memory preserved)."

        elif cmd == "/session":
            return (
                f"Session: {self.session_id}\n"
                f"  Messages in context: {len(self.messages)}\n"
                f"  Compressed history: {'yes' if self._compressed_context else 'no'}\n"
                f"  Models: {cfg.model} / {cfg.model_light}\n"
                f"  Tools: {', '.join(registry.tool_names)}"
            )

        elif cmd == "/help":
            return (
                "Commands:\n"
                "  /memory  — Show all stored facts\n"
                "  /clear   — Clear conversation context\n"
                "  /session — Show session info\n"
                "  /help    — This message"
            )

        return f"Unknown command: {command}. Type /help for options."

    async def _end_session(self) -> None:
        if len(self.messages) >= 4:
            try:
                summary = await self.brain.summarize_history(self.messages)
                self.memory.save_summary(self.session_id, summary)
            except Exception:
                pass

        self.memory.close()
        print(f"\n  {cfg.name}: Session ended. See you next time.\n")