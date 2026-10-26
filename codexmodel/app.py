"""Minimal API surface for the Codexmodel assistant runtime.

This starter intentionally does not fabricate model responses. Configure a real
provider adapter before enabling model-backed chat.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Codexmodel",
    description="A provider-neutral, safety-first assistant runtime.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)


class ChatResponse(BaseModel):
    status: str
    message: str
    session_id: str | None = None
    provider: str | None = None


def capability_snapshot() -> dict[str, Any]:
    """Report implemented features without overstating unfinished capabilities."""
    provider = os.getenv("CODEXMODEL_PROVIDER", "").strip()
    return {
        "conversation_api": True,
        "provider_configured": bool(provider),
        "provider": provider or None,
        "persistent_memory": False,
        "tool_execution": False,
        "image_input": False,
        "audio_input": False,
        "file_ingestion": False,
        "notes": [
            "Model-backed responses require a provider adapter.",
            "No model-generated content is executed as code.",
            "Unimplemented capabilities are reported as unavailable.",
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
    """Fail closed until a real model provider is configured and integrated."""
    if not os.getenv("CODEXMODEL_PROVIDER", "").strip():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "provider_not_configured",
                "message": (
                    "No model provider is configured. Add a supported provider adapter "
                    "before requesting model-generated responses."
                ),
            },
        )
    # A provider name alone is not enough to safely generate a response.
    raise HTTPException(
        status_code=501,
        detail={
            "code": "provider_adapter_not_implemented",
            "message": (
                "Provider configuration was detected, but provider adapters are not "
                "implemented yet. No fabricated response was returned."
            ),
        },
    )
