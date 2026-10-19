"""
Persona tool — allows Tadashi to modify its own personality and communication style.
"""

from tools.registry import BaseTool, register_tool

_memory = None


def set_memory(mem) -> None:
    global _memory
    _memory = mem


@register_tool
class UpdatePersonaTool(BaseTool):
    name = "update_persona"
    description = (
        "Update your own personality, tone, or communication style. Use this whenever "
        "the user asks you to change how you talk, act, or present yourself. Write the "
        "new persona as a complete system prompt paragraph describing who you are and "
        "how you communicate. Be thorough — this replaces your entire personality definition. "
        "Include specific behavioral instructions like tone, formality level, humor style, "
        "vocabulary, and how you address the user."
    )
    parameters = {
        "type": "object",
        "properties": {
            "persona": {
                "type": "string",
                "description": (
                    "The complete new persona description. Write it as instructions to yourself. "
                    "Example: 'You are Tadashi. You talk like a close friend — casual, relaxed, "
                    "uses slang naturally. You keep things short and real. No corporate speak, "
                    "no filler, no formality unless the situation genuinely calls for it.'"
                ),
            },
            "reason": {
                "type": "string",
                "description": "Brief note on what the user asked for, for logging.",
            },
        },
        "required": ["persona", "reason"],
    }

    async def execute(self, persona: str, reason: str = "", **kwargs) -> str:
        if _memory is None:
            return "Memory system not initialized."
        _memory.set_fact("custom_persona", persona, "system")
        _memory.set_fact("persona_change_reason", reason, "system")
        return (
            f"Persona updated. This takes effect on the next message. "
            f"Reason: {reason}"
        )


@register_tool
class GetPersonaTool(BaseTool):
    name = "get_persona"
    description = (
        "Retrieve your current persona/personality settings. Use this if the user "
        "asks how you're configured or what your current style is."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        if _memory is None:
            return "Memory system not initialized."
        persona = _memory.get_fact("custom_persona")
        if persona:
            reason = _memory.get_fact("persona_change_reason") or "no reason logged"
            return f"Current persona:\n{persona}\n\nLast changed because: {reason}"
        return "Using default persona (no custom persona set)."