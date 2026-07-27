from uuid import uuid4

import pytest

from app.application.use_cases.detect_signals import DetectSignals
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.domain.services.signal_detection_service import SignalDetectionService
from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
from app.infrastructure.repositories.sqlalchemy_scoring_config_repo import (
    SqlAlchemyScoringConfigRepository,
)
from app.infrastructure.repositories.sqlalchemy_signal_repo import SqlAlchemySignalRepository
from tests.support.fakes import FakeClinicSource, FakeWebsiteCrawler, make_clinic_data

HIRING_HTML = "<html><body>We are hiring a receptionist</body></html>"
ADVERTISING_HTML = "<html><script>gtag('config', 'AW-123');</script></html>"


@pytest.fixture
def signal_stack(db_session):
    clinic_repo = SqlAlchemyClinicRepository(db_session)
    signal_repo = SqlAlchemySignalRepository(db_session)
    scoring_repo = SqlAlchemyScoringConfigRepository(db_session)
    crawler = FakeWebsiteCrawler()
    detect = DetectSignals(
        clinic_repo,
        signal_repo,
        scoring_repo,
        crawler,
        SignalDetectionService(),
    )
    return clinic_repo, signal_repo, crawler, detect


def _seed_clinic(clinic_repo, website: str = "https://clinic.example"):
    source = FakeClinicSource([make_clinic_data(place_id=f"place-{uuid4()}", website=website)])
    DiscoverClinics(source, clinic_repo).execute("dentist")
    return clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic


def test_detect_persists_signals_with_weights(signal_stack):
    clinic_repo, signal_repo, crawler, detect = signal_stack
    clinic = _seed_clinic(clinic_repo)
    crawler.set_page(clinic.website, HIRING_HTML)

    result = detect.execute(clinic.id)
    assert result.detected == 1
    assert result.signals[0].applied_weight == 25
    assert result.signals[0].type.value == "HIRING"

    listed = signal_repo.list_by_clinic(clinic.id)
    assert len(listed) == 1


def test_detect_replace_same_type_on_rerun(signal_stack):
    clinic_repo, signal_repo, crawler, detect = signal_stack
    clinic = _seed_clinic(clinic_repo)
    crawler.set_page(clinic.website, HIRING_HTML)
    detect.execute(clinic.id)

    crawler.set_page(clinic.website, ADVERTISING_HTML)
    result = detect.execute(clinic.id)

    assert result.detected == 1
    listed = signal_repo.list_by_clinic(clinic.id)
    assert len(listed) == 1
    assert listed[0].type.value == "ADVERTISING"


def test_detect_endpoint(client, db_session, signal_stack):
    clinic_repo, _signal_repo, crawler, detect = signal_stack
    clinic = _seed_clinic(clinic_repo)
    crawler.set_page(clinic.website, HIRING_HTML)

    from app.main import create_app
    from app.presentation.api.deps import get_db_session, get_detect_signals

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_detect_signals] = lambda: detect

    from fastapi.testclient import TestClient

    with TestClient(app) as api_client:
        response = api_client.post(f"/api/v1/clinics/{clinic.id}/signals:detect")
        assert response.status_code == 200
        body = response.json()
        assert body["detected"] == 1
        assert body["signals"][0]["type"] == "HIRING"
        assert body["signals"][0]["applied_weight"] == 25

        list_response = api_client.get(f"/api/v1/clinics/{clinic.id}/signals")
        assert list_response.status_code == 200
        assert len(list_response.json()["data"]) == 1

    app.dependency_overrides.clear()


def test_detect_not_found(client):
    response = client.post(f"/api/v1/clinics/{uuid4()}/signals:detect")
    assert response.status_code == 404
