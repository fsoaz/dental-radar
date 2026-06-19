from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.application.use_cases.compute_score import ComputeScore
from app.application.use_cases.detect_signals import DetectSignals
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.domain.entities.signal import Signal
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.domain.services.signal_detection_service import SignalDetectionService
from app.domain.value_objects.signal_type import SignalType
from app.infrastructure.repositories.sqlalchemy_score_repo import SqlAlchemyScoreRepository
from app.infrastructure.repositories.sqlalchemy_scoring_config_repo import (
    SqlAlchemyScoringConfigRepository,
)
from app.infrastructure.repositories.sqlalchemy_signal_repo import SqlAlchemySignalRepository
from tests.support.fakes import FakeClinicSource, FakeWebsiteCrawler, make_clinic_data

HIRING_HTML = "<html><body>We are hiring a receptionist</body></html>"


@pytest.fixture
def scoring_stack(db_session):
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository

    clinic_repo = SqlAlchemyClinicRepository(db_session)
    signal_repo = SqlAlchemySignalRepository(db_session)
    score_repo = SqlAlchemyScoreRepository(db_session)
    scoring_repo = SqlAlchemyScoringConfigRepository(db_session)
    crawler = FakeWebsiteCrawler()
    detect = DetectSignals(
        clinic_repo,
        signal_repo,
        scoring_repo,
        crawler,
        SignalDetectionService(),
    )
    compute = ComputeScore(clinic_repo, signal_repo, score_repo, scoring_repo)
    return clinic_repo, signal_repo, score_repo, scoring_repo, crawler, detect, compute


def _seed_scored_clinic(scoring_stack, html: str = HIRING_HTML):
    clinic_repo, _signal_repo, _score_repo, _scoring_repo, crawler, detect, compute = scoring_stack
    source = FakeClinicSource([make_clinic_data(place_id=f"score-{uuid4()}")])
    DiscoverClinics(source, clinic_repo).execute("dentist")
    clinic = clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic
    crawler.set_page(clinic.website, html)
    detect.execute(clinic.id)
    compute.execute(clinic.id)
    return clinic


def test_compute_score_persists_breakdown(scoring_stack):
    clinic = _seed_scored_clinic(scoring_stack)
    _clinic_repo, _signal_repo, score_repo, _scoring_repo, *_rest = scoring_stack
    score = score_repo.get_by_clinic(clinic.id)
    assert score is not None
    assert score.total == 25
    assert score.priority.value == "COLD"
    assert score.breakdown.to_dict()["HIRING"] == 25


def test_compute_score_endpoint(client, db_session, scoring_stack):
    clinic = _seed_scored_clinic(scoring_stack)
    *_rest, compute = scoring_stack

    from app.main import create_app
    from app.presentation.api.deps import get_compute_score, get_db_session

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_compute_score] = lambda: compute

    from fastapi.testclient import TestClient

    with TestClient(app) as api_client:
        response = api_client.post(f"/api/v1/clinics/{clinic.id}/score")
        assert response.status_code == 202
        body = response.json()
        assert body["total"] == 25
        assert body["breakdown"]["HIRING"] == 25

        detail = api_client.get(f"/api/v1/clinics/{clinic.id}")
        assert detail.json()["score"]["breakdown"]["HIRING"] == 25

    app.dependency_overrides.clear()


def test_list_clinics_sorts_by_score(scoring_stack):
    clinic_repo, signal_repo, *_rest = scoring_stack
    _seed_scored_clinic(scoring_stack)
    high_clinic = make_clinic_data(place_id=f"high-{uuid4()}", name="High Score Clinic")
    DiscoverClinics(FakeClinicSource([high_clinic]), clinic_repo).execute("dentist")
    high = clinic_repo.list_clinics(ClinicListQuery(q="High Score")).items[0].clinic

    compute = scoring_stack[6]

    signal_repo.replace_for_clinic(
        high.id,
        [
            Signal(
                id=uuid4(),
                clinic_id=high.id,
                type=SignalType.HIRING,
                applied_weight=25,
                evidence="hiring",
                confidence=1.0,
                detected_at=datetime.now(UTC),
            ),
            Signal(
                id=uuid4(),
                clinic_id=high.id,
                type=SignalType.ADVERTISING,
                applied_weight=30,
                evidence="ads",
                confidence=1.0,
                detected_at=datetime.now(UTC),
            ),
            Signal(
                id=uuid4(),
                clinic_id=high.id,
                type=SignalType.WEBSITE_QUALITY,
                applied_weight=15,
                evidence="site",
                confidence=1.0,
                detected_at=datetime.now(UTC),
            ),
        ],
    )
    compute.execute(high.id)

    ranked = clinic_repo.list_clinics(ClinicListQuery(sort="-score", page_size=10))
    assert ranked.items[0].clinic.id == high.id
    assert ranked.items[0].score == 70


def test_update_scoring_config_rescores(client, db_session, scoring_stack):
    clinic = _seed_scored_clinic(scoring_stack)
    clinic_repo, _signal_repo, score_repo, scoring_repo, *_rest, compute = scoring_stack

    from app.application.use_cases.compute_score import RescoreAll, UpdateScoringConfig
    from app.main import create_app
    from app.presentation.api.deps import get_db_session, get_update_scoring_config

    rescore_all = RescoreAll(clinic_repo, compute)
    update = UpdateScoringConfig(scoring_repo, rescore_all)

    app = create_app()

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_update_scoring_config] = lambda: update

    from fastapi.testclient import TestClient

    with TestClient(app) as api_client:
        response = api_client.put(
            "/api/v1/scoring-config",
            json={
                "weights": {
                    "HIRING": 60,
                    "ADVERTISING": 30,
                    "WEBSITE_QUALITY": 15,
                    "MULTI_LOCATION": 40,
                    "HIGH_TICKET": 20,
                },
                "bands": [
                    {"name": "COLD", "min": 0, "max": 50},
                    {"name": "WARM", "min": 51, "max": 100},
                    {"name": "HOT", "min": 101, "max": 150},
                    {"name": "IMMEDIATE", "min": 151, "max": None},
                ],
                "rescore": True,
            },
        )
        assert response.status_code == 200

    score = score_repo.get_by_clinic(clinic.id)
    assert score is not None
    assert score.total == 60
    assert score.config_version == 2

    app.dependency_overrides.clear()
