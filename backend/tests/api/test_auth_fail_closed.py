"""Auth fail-closed behaviour (QA §9.5)."""

from fastapi.testclient import TestClient

from app.infrastructure.config import settings as settings_module
from app.main import create_app
from app.presentation.api.deps import get_db_session


def test_empty_api_key_fails_closed_without_escape_hatch(db_session, monkeypatch):
    monkeypatch.setattr(settings_module.settings, "api_key", "")
    monkeypatch.setattr(settings_module.settings, "allow_unauthenticated", False)
    monkeypatch.setattr(settings_module.settings, "app_env", "development")

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db

    with TestClient(app) as client:
        response = client.put(
            "/api/v1/scoring-config",
            json={
                "weights": {
                    "HIRING": 25,
                    "ADVERTISING": 30,
                    "WEBSITE_QUALITY": 15,
                    "MULTI_LOCATION": 40,
                    "HIGH_TICKET": 20,
                },
                "bands": [{"name": "COLD", "min": 0, "max": None}],
            },
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "API_KEY_NOT_CONFIGURED"

    app.dependency_overrides.clear()


def test_configured_api_key_rejects_missing_header(db_session, monkeypatch):
    monkeypatch.setattr(settings_module.settings, "api_key", "secret-operator-key")
    monkeypatch.setattr(settings_module.settings, "allow_unauthenticated", False)
    monkeypatch.setattr(settings_module.settings, "app_env", "development")

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db

    with TestClient(app) as client:
        response = client.post("/api/v1/clinics/discover", json={"query": "dentist"})
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"

        ok_key = client.post(
            "/api/v1/clinics/discover",
            json={"query": "dentist"},
            headers={"X-API-Key": "secret-operator-key"},
        )
        # 503 if Places key missing, or 200 if overridden — never 401 with valid key.
        assert ok_key.status_code != 401

    app.dependency_overrides.clear()
