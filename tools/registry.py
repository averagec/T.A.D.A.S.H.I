"""
Tool registry — the backbone of Jarvis's capabilities.

Define a tool by subclassing BaseTool. The registry auto-discovers all tools
in the tools/ package. Each tool declares its Claude function-calling schema
and an execute() method.

Example:
    class WeatherTool(BaseTool):
        name = "get_weather"
        description = "Get current weather for a location"
        parameters = {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name or coordinates"}
            },
            "required": ["location"]
        }

        async def execute(self, **kwargs) -> str:
            ...
"""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for all Jarvis tools."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Run the tool and return a string result for the LLM."""
        ...

    def to_schema(self) -> dict[str, Any]:
        """Convert to Claude's tool-use schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


class ToolRegistry:
    """Discovers and manages all available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError(f"{tool.__class__.__name__} has no 'name' set")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    async def execute(self, name: str, **kwargs) -> str:
        tool = self.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'"
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return f"Error running {name}: {e}"

    def schemas(self) -> list[dict[str, Any]]:
        """All tool schemas for the Claude API call."""
        return [t.to_schema() for t in self._tools.values()]

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def auto_discover(self) -> None:
        """Import all modules in the tools package so tools self-register."""
        import tools as tools_pkg

        for _, module_name, _ in pkgutil.iter_modules(tools_pkg.__path__):
            if module_name == "registry":
                continue
            importlib.import_module(f"tools.{module_name}")


# Global registry instance
registry = ToolRegistry()


def register_tool(cls: type[BaseTool]) -> type[BaseTool]:
    """Class decorator — register a tool just by decorating it."""
    registry.register(cls())
    return cls
