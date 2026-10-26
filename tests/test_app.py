from fastapi.testclient import TestClient

from codexmodel.app import app, capability_snapshot

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "codexmodel"}


def test_capabilities_do_not_overstate_features() -> None:
    data = capability_snapshot()
    assert data["conversation_api"] is True
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
