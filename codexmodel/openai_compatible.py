"""OpenAI-compatible chat-completions adapter, usable with hosted or local endpoints."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from codexmodel.providers import ChatMessage, ModelReply


class ProviderError(RuntimeError):
    """Safe-to-report provider failure; never contains credentials or response bodies."""


class OpenAICompatibleProvider:
    """Minimal synchronous adapter for /v1/chat/completions-compatible APIs."""

    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_response_bytes: int = 1_000_000,
    ) -> None:
        normalized_url = base_url.strip().rstrip("/")
        if not normalized_url.startswith(("https://", "http://")):
            raise ValueError("CODEXMODEL_BASE_URL must be an http(s) URL")
        if not model.strip():
            raise ValueError("CODEXMODEL_MODEL must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = normalized_url
        self.model = model.strip()
        self.api_key = api_key.strip() if api_key and api_key.strip() else None
        self.timeout = timeout
        self.max_response_bytes = max_response_bytes

    @classmethod
    def from_env(cls) -> "OpenAICompatibleProvider":
        base_url = os.getenv("CODEXMODEL_BASE_URL", "").strip()
        model = os.getenv("CODEXMODEL_MODEL", "").strip()
        if not base_url or not model:
            raise ValueError(
                "Set CODEXMODEL_BASE_URL and CODEXMODEL_MODEL for the configured provider."
            )
        try:
            timeout = float(os.getenv("CODEXMODEL_TIMEOUT_SECONDS", "30"))
        except ValueError as exc:
            raise ValueError("CODEXMODEL_TIMEOUT_SECONDS must be a number") from exc
        return cls(
            base_url=base_url,
            model=model,
            api_key=os.getenv("CODEXMODEL_API_KEY"),
            timeout=timeout,
        )

    def generate(self, messages: list[ChatMessage]) -> ModelReply:
        if not messages:
            raise ProviderError("At least one chat message is required.")
        payload = {
            "model": self.model,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            "stream": False,
        }
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            raise ProviderError(f"Provider returned HTTP {exc.code}.") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError("Could not reach the configured model provider.") from None
        if len(raw) > self.max_response_bytes:
            raise ProviderError("Provider response exceeded the configured size limit.")
        try:
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider returned an invalid chat-completions response.") from None
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Provider returned an empty or unsupported response.")
        return ModelReply(content=content, provider=self.name, model=self.model)
