"""Provider adapter contracts; concrete network/local adapters belong in separate modules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ModelReply:
    content: str
    provider: str
    model: str | None = None


class ModelProvider(Protocol):
    """Minimal interface implemented by a real model backend."""

    @property
    def name(self) -> str:
        """Stable provider identifier."""

    def generate(self, messages: list[ChatMessage]) -> ModelReply:
        """Generate a reply or raise a typed provider error.

        Implementations must apply timeouts, bound input/output, avoid leaking
        credentials, and treat retrieved content as untrusted data.
        """
