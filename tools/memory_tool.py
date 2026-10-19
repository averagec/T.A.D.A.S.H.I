"""
Memory tool — allows the LLM to save and recall facts about the user.

This is how Jarvis "learns" — the brain calls this tool when the user shares
something worth remembering (name, preferences, routines, etc.)
"""

from tools.registry import BaseTool, register_tool

# The actual memory instance gets injected at startup via set_memory()
_memory = None


def set_memory(mem) -> None:
    global _memory
    _memory = mem


@register_tool
class SaveFactTool(BaseTool):
    name = "save_fact"
    description = (
        "Save a fact about the user to persistent memory. Use this when the user "
        "tells you something worth remembering — their name, preferences, routines, "
        "important dates, or anything that would be useful in future conversations. "
        "Categories: 'identity' (name, age, location), 'preference' (likes, dislikes, "
        "settings), 'context' (projects, goals, situations), 'system' (configuration)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "Short descriptive key, e.g. 'user_name', 'favorite_food', 'works_at'",
            },
            "value": {
                "type": "string",
                "description": "The fact to remember",
            },
            "category": {
                "type": "string",
                "enum": ["identity", "preference", "context", "system"],
                "description": "Category for organization",
            },
        },
        "required": ["key", "value", "category"],
    }

    async def execute(self, key: str, value: str, category: str = "context", **kwargs) -> str:
        if _memory is None:
            return "Memory system not initialized."
        _memory.set_fact(key, value, category)
        return f"Saved: {key} = {value} [{category}]"


@register_tool
class RecallFactsTool(BaseTool):
    name = "recall_facts"
    description = (
        "Retrieve stored facts about the user. Use this when you need to look up "
        "something specific about the user that might be in memory, or to check "
        "what you know about them. Can filter by category."
    )
    parameters = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["identity", "preference", "context", "system", "all"],
                "description": "Which category to retrieve. Use 'all' for everything.",
            },
        },
        "required": [],
    }

    async def execute(self, category: str = "all", **kwargs) -> str:
        if _memory is None:
            return "Memory system not initialized."

        if category == "all":
            facts = _memory.get_all_facts()
        else:
            facts = _memory.get_facts_by_category(category)

        if not facts:
            return f"No facts stored{f' in category {category}' if category != 'all' else ''}."

        lines = []
        for f in facts:
            lines.append(f"  [{f.category}] {f.key}: {f.value}")
        return "Stored facts:\n" + "\n".join(lines)
