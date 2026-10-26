from __future__ import annotations

import json
from io import BytesIO

from fastapi.testclient import TestClient

from codexmodel.app import app, capability_snapshot
from codexmodel.openai_compatible import OpenAICompatibleProvider, ProviderError

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "codexmodel"}


def test_capabilities_do_not_overstate_features(monkeypatch) -> None:
    monkeypatch.delenv("CODEXMODEL_PROVIDER", raising=False)
    data = capability_snapshot()
    assert data["conversation_api"] is True
    assert data["provider_configured"] is False
    assert data["tool_execution"] is False
    assert data["image_input"] is False
    assert data["audio_input"] is False


def test_chat_fails_closed_without_provider(monkeypatch) -> None:
    monkeypatch.delenv("CODEXMODEL_PROVIDER", raising=False)
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_not_configured"


def test_chat_rejects_empty_message() -> None:
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422


def test_provider_configuration_requires_url_and_model(monkeypatch) -> None:
    monkeypatch.setenv("CODEXMODEL_PROVIDER", "openai_compatible")
    monkeypatch.delenv("CODEXMODEL_BASE_URL", raising=False)
    monkeypatch.delenv("CODEXMODEL_MODEL", raising=False)
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "provider_not_configured"


def test_chat_returns_real_adapter_reply_when_provider_is_mocked(monkeypatch) -> None:
    monkeypatch.setenv("CODEXMODEL_PROVIDER", "openai_compatible")
    monkeypatch.setenv("CODEXMODEL_BASE_URL", "http://localhost:1234/v1")
    monkeypatch.setenv("CODEXMODEL_MODEL", "local-test-model")

    def fake_generate(self, messages):
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        from codexmodel.providers import ModelReply
        return ModelReply("Hi from the test provider", "openai_compatible", "local-test-model")

    monkeypatch.setattr(OpenAICompatibleProvider, "generate", fake_generate)
    response = client.post("/chat", json={"message": "Hello", "session_id": "test-session"})
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Hi from the test provider",
        "session_id": "test-session",
        "provider": "openai_compatible",
    }


def test_adapter_parses_chat_completions_response(monkeypatch) -> None:
    class FakeResponse(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    import codexmodel.openai_compatible as adapter_module

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(b'{"choices":[{"message":{"content":"Model answer"}}]}')

    monkeypatch.setattr(adapter_module, "urlopen", fake_urlopen)
    provider = OpenAICompatibleProvider(
        base_url="http://127.0.0.1:1234/v1/",
        model="test-model",
        api_key="test-secret",
    )
    reply = provider.generate([__import__("codexmodel.providers", fromlist=["ChatMessage"]).ChatMessage("user", "Hello")])
    assert reply.content == "Model answer"
    assert captured["url"] == "http://127.0.0.1:1234/v1/chat/completions"
    assert captured["body"]["model"] == "test-model"


def test_adapter_does_not_expose_provider_error_body(monkeypatch) -> None:
    from urllib.error import URLError
    import codexmodel.openai_compatible as adapter_module

    def fail_urlopen(request, timeout):
        raise URLError("secret-bearing network detail")

    monkeypatch.setattr(adapter_module, "urlopen", fail_urlopen)
    provider = OpenAICompatibleProvider(base_url="http://localhost/v1", model="test")
    try:
        provider.generate([__import__("codexmodel.providers", fromlist=["ChatMessage"]).ChatMessage("user", "Hello")])
    except ProviderError as exc:
        assert "secret-bearing" not in str(exc)
    else:
        raise AssertionError("ProviderError was not raised")
