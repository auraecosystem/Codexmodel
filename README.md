# Codexmodel

Codexmodel is an independently built, extensible AI assistant runtime. It provides a practical foundation for conversational AI and explicitly configured model-provider integrations.

> **Scope and honesty:** Codexmodel does not contain or reproduce ChatGPT's private model weights, hidden instructions, proprietary services, or internal runtime. It implements its own interfaces and integrations and requires an explicitly configured model endpoint for model-backed responses.

## Current implementation

- FastAPI endpoints: `GET /health`, `GET /capabilities`, and `POST /chat`.
- An OpenAI-compatible `/chat/completions` adapter, usable with a local or hosted endpoint.
- Server-side optional bearer-token configuration; credentials are never returned by the API.
- Bounded request and response sizes, configurable request timeout, and sanitized provider errors.
- Explicit capability reporting. Persistent memory, tool execution, image/audio input, and file ingestion remain unavailable.
- Pytest and Ruff checks in GitHub Actions.

## Quick start

Requirements: Python 3.11 or newer.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env
```

Set these environment variables in your shell or deployment environment (the app does not automatically load `.env`):

- `CODEXMODEL_PROVIDER=openai_compatible`
- `CODEXMODEL_BASE_URL=http://127.0.0.1:1234/v1` (example local endpoint)
- `CODEXMODEL_MODEL=your-model-id`
- `CODEXMODEL_API_KEY` only if your endpoint requires it
- `CODEXMODEL_TIMEOUT_SECONDS=30` (optional)

Run the API:

```bash
uvicorn codexmodel.app:app --reload
```

Example request:

```bash
curl -s http://127.0.0.1:8000/chat \\\
  -H 'Content-Type: application/json' \\\
  -d '{"message":"Hello"}'
```

Run checks:

```bash
pytest
ruff check .
```

## Architecture and next layers

1. **API/runtime:** health, capabilities, chat.
2. **Model adapter:** synchronous OpenAI-compatible chat-completions interface.
3. **Tools:** allowlisted registry exists as a separate foundation but is not connected to chat.
4. **Memory:** session history is not persisted.
5. **Multimodal content:** image, audio, and file inputs are not implemented.
6. **Operations:** add authentication, rate limiting, deployment controls, and integration tests before public exposure.

## Security notes

- Keep provider credentials server-side and out of source control.
- Bind to localhost during development; do not expose this API publicly without authentication, TLS, and rate limiting.
- Only send requests to a provider endpoint you trust. The configured endpoint receives the user's message.
- Model output is returned as text and is never executed as code.
- Provider response bodies and network details are not forwarded in API errors.

## License

No license is declared yet. Until a license file is added, do not assume the code is available for reuse under an open-source license.
