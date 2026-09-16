from uuid import uuid4

import pytest

from app.application.dto.enrichment_dto import ClinicAIInput
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.application.use_cases.enrich_clinic import EnrichClinic
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.infrastructure.repositories.sqlalchemy_enrichment_repo import (
    SqlAlchemyEnrichmentRepository,
)
from tests.support.fakes import (
    FakeClinicSource,
    FakeLLMProvider,
    FakeWebsiteCrawler,
    make_clinic_data,
)


@pytest.fixture
def enrichment_stack(db_session):
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository

    clinic_repo = SqlAlchemyClinicRepository(db_session)
    enrichment_repo = SqlAlchemyEnrichmentRepository(db_session)
    crawler = FakeWebsiteCrawler()
    llm = FakeLLMProvider()
    enrich = EnrichClinic(clinic_repo, enrichment_repo, crawler, llm, 8000)
    return clinic_repo, enrichment_repo, crawler, llm, enrich


def _seed_clinic(enrichment_stack, *, website: str = "https://smile.example"):
    clinic_repo, *_rest = enrichment_stack
    source = FakeClinicSource([make_clinic_data(place_id=f"enrich-{uuid4()}", website=website)])
    DiscoverClinics(source, clinic_repo).execute("dentist")
    return clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic


def test_enrich_clinic_persists_scores(enrichment_stack):
    clinic = _seed_clinic(enrichment_stack)
    _clinic_repo, enrichment_repo, crawler, llm, enrich = enrichment_stack
    crawler.set_page(clinic.website, "<html><body>Implants and Invisalign</body></html>")

    result = enrich.execute(clinic.id)
    assert result.skipped is False
    assert result.growth_probability == 78
    assert result.provider == "fake"

    stored = enrichment_repo.get_by_clinic(clinic.id)
    assert stored is not None
    assert stored.prompt_version == "clinic_enrichment_v1"
    assert stored.input_fingerprint
    assert llm.payloads[0].name == clinic.name


def test_enrich_clinic_skips_when_unchanged(enrichment_stack):
    clinic = _seed_clinic(enrichment_stack)
    *_rest, enrich = enrichment_stack

    first = enrich.execute(clinic.id)
    second = enrich.execute(clinic.id)

    assert first.skipped is False
    assert second.skipped is True
    assert second.skip_reason == "Inputs unchanged"


def test_enrich_clinic_force_reruns(enrichment_stack):
    clinic = _seed_clinic(enrichment_stack)
    llm = enrichment_stack[3]
    enrich = enrichment_stack[4]

    enrich.execute(clinic.id)
    enrich.execute(clinic.id, force=True)

    assert len(llm.payloads) == 2


def test_enrich_clinic_continues_without_site_text_after_crawl_failure(enrichment_stack):
    clinic = _seed_clinic(enrichment_stack)
    crawler = enrichment_stack[2]
    llm = enrichment_stack[3]
    enrich = enrichment_stack[4]
    crawler.fail(clinic.website)

    result = enrich.execute(clinic.id)

    assert result.skipped is False
    assert llm.payloads[0].site_text == ""


def test_enrich_clinic_endpoint(client, db_session, enrichment_stack):
    clinic = _seed_clinic(enrichment_stack)
    *_rest, enrich = enrichment_stack

    from app.main import create_app
    from app.presentation.api.deps import get_db_session, get_enrich_clinic

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_enrich_clinic] = lambda: enrich

    from fastapi.testclient import TestClient

    with TestClient(app) as api_client:
        response = api_client.post(f"/api/v1/clinics/{clinic.id}/enrich")
        assert response.status_code == 200
        body = response.json()
        assert body["growth_probability"] == 78
        assert body["provider"] == "fake"

        detail = api_client.get(f"/api/v1/clinics/{clinic.id}")
        assert detail.json()["enrichment"]["growth_probability"] == 78

        listed = api_client.get("/api/v1/clinics")
        assert listed.json()["data"][0]["growth_probability"] == 78

    app.dependency_overrides.clear()


def test_enrich_clinic_not_found(client):
    missing_id = uuid4()
    response = client.post(f"/api/v1/clinics/{missing_id}/enrich")
    assert response.status_code == 404


def test_enrich_clinic_provider_failure_maps_to_safe_502(db_session):
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
    from app.main import create_app
    from app.presentation.api.deps import get_db_session, get_enrich_clinic

    class _FailingProvider:
        provider_name = "fake"
        model_name = "fake-model"

        def analyze_clinic(self, payload: ClinicAIInput):
            raise RuntimeError(f"secret upstream response for {payload.name}")

    clinic_repo = SqlAlchemyClinicRepository(db_session)
    enrichment_repo = SqlAlchemyEnrichmentRepository(db_session)
    crawler = FakeWebsiteCrawler()
    enrich = EnrichClinic(clinic_repo, enrichment_repo, crawler, _FailingProvider(), 8000)
    source = FakeClinicSource([make_clinic_data(place_id=f"enrich-failure-{uuid4()}")])
    DiscoverClinics(source, clinic_repo).execute("dentist")
    clinic = clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic

    app = create_app()

    def override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_enrich_clinic] = lambda: enrich

    from fastapi.testclient import TestClient

    with TestClient(app) as api_client:
        response = api_client.post(f"/api/v1/clinics/{clinic.id}/enrich")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ENRICHMENT_FAILED"
    assert "secret upstream" not in response.text
    app.dependency_overrides.clear()


def test_invalid_ai_provider_maps_to_enrichment_failed(client, db_session, monkeypatch):
    from app.infrastructure.config.settings import settings
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository

    clinic_repo = SqlAlchemyClinicRepository(db_session)
    source = FakeClinicSource(
        [make_clinic_data(place_id=f"invalid-provider-{uuid4()}", website="")]
    )
    DiscoverClinics(source, clinic_repo).execute("dentist")
    clinic = clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic

    monkeypatch.setattr(settings, "ai_provider", "bogus")
    monkeypatch.setattr(settings, "ai_fallback_provider", "")

    response = client.post(f"/api/v1/clinics/{clinic.id}/enrich")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ENRICHMENT_FAILED"
    assert "Unsupported AI provider" not in response.text
