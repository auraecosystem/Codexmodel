"""Minimal API surface for the Codexmodel assistant runtime."""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from codexmodel.openai_compatible import OpenAICompatibleProvider, ProviderError
from codexmodel.providers import ChatMessage

app = FastAPI(
    title="Codexmodel",
    description="A provider-neutral, safety-first assistant runtime.",
    version="0.2.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)


class ChatResponse(BaseModel):
    status: str
    message: str
    session_id: str | None = None
    provider: str | None = None


def configured_provider() -> OpenAICompatibleProvider:
    """Build only the provider explicitly selected in environment configuration."""
    provider_name = os.getenv("CODEXMODEL_PROVIDER", "").strip().lower()
    if provider_name != "openai_compatible":
        raise ValueError(
            "CODEXMODEL_PROVIDER must be set to 'openai_compatible' to enable chat."
        )
    return OpenAICompatibleProvider.from_env()


def capability_snapshot() -> dict[str, Any]:
    """Report implemented features without overstating unfinished capabilities."""
    provider_name = os.getenv("CODEXMODEL_PROVIDER", "").strip().lower()
    provider_ready = False
    if provider_name == "openai_compatible":
        try:
            configured_provider()
            provider_ready = True
        except ValueError:
            pass
    return {
        "conversation_api": True,
        "provider_configured": provider_ready,
        "provider": provider_name if provider_ready else None,
        "persistent_memory": False,
        "tool_execution": False,
        "image_input": False,
        "audio_input": False,
        "file_ingestion": False,
        "notes": [
            "Chat supports the explicitly configured OpenAI-compatible chat-completions API.",
            "A local or hosted endpoint must be configured; API keys stay server-side.",
            "No model-generated content is executed as code.",
            "Persistent memory, tools, image/audio input, and file ingestion are not wired in.",
        ],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "codexmodel"}


@app.get("/capabilities")
def capabilities() -> dict[str, Any]:
    return capability_snapshot()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Generate a response using the explicitly configured provider."""
    try:
        provider = configured_provider()
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "provider_not_configured", "message": str(exc)},
        ) from None

    try:
        reply = provider.generate([ChatMessage(role="user", content=request.message)])
    except ProviderError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "provider_request_failed", "message": str(exc)},
        ) from None

    return ChatResponse(
        status="ok",
        message=reply.content,
        session_id=request.session_id,
        provider=reply.provider,
    )
