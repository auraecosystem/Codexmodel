"""Small allowlisted tool registry; intentionally excludes arbitrary shell execution."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class ToolError(Exception):
    """Raised when a tool is unknown, disabled, or fails validation."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    enabled: bool = True
    requires_approval: bool = True


class ToolRegistry:
    """Only explicitly registered tools can be invoked."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name or not tool.name.replace("_", "").isalnum():
            raise ValueError("Tool names must be non-empty alphanumeric identifiers.")
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "enabled": tool.enabled,
                "requires_approval": tool.requires_approval,
            }
            for tool in sorted(self._tools.values(), key=lambda item: item.name)
        ]

    def invoke(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        approved: bool = False,
    ) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(f"Unknown tool: {name}")
        if not tool.enabled:
            raise ToolError(f"Tool is disabled: {name}")
        if tool.requires_approval and not approved:
            raise ToolError(f"Explicit approval is required for tool: {name}")
        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be a JSON object.")
        try:
            result = tool.handler(arguments)
        except ToolError:
            raise
        except Exception as exc:
            # Do not leak internal exception details to the caller.
            raise ToolError(f"Tool failed: {name}") from exc
        if not isinstance(result, dict):
            raise ToolError("Tool handlers must return a JSON object.")
        return result
