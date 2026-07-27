from collections.abc import Generator
from secrets import compare_digest

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.application.use_cases.compute_score import (
    ComputeScore,
    GetScoringConfig,
    RescoreAll,
    UpdateScoringConfig,
)
from app.application.use_cases.detect_all_signals import DetectAllSignals
from app.application.use_cases.detect_signals import DetectSignals, ListClinicSignals
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.application.use_cases.enrich_clinic import EnrichAllClinics, EnrichClinic
from app.application.use_cases.list_clinics import GetClinic, ListClinics
from app.domain.exceptions import ApiKeyNotConfiguredError, UnauthorizedError
from app.infrastructure.config.settings import settings
from app.infrastructure.crawler.website_crawler import HttpxWebsiteCrawler
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
from app.infrastructure.repositories.sqlalchemy_enrichment_repo import (
    SqlAlchemyEnrichmentRepository,
)
from app.infrastructure.repositories.sqlalchemy_score_repo import SqlAlchemyScoreRepository
from app.infrastructure.repositories.sqlalchemy_scoring_config_repo import (
    SqlAlchemyScoringConfigRepository,
)
from app.infrastructure.repositories.sqlalchemy_signal_repo import SqlAlchemySignalRepository
from app.infrastructure.sources.google_places import GooglePlacesClient


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Gate mutating routes behind X-API-Key.

    Fails closed: an empty API_KEY rejects with 503 unless
    ``ALLOW_UNAUTHENTICATED=true`` is set explicitly (local/test only).
    Relying on ``APP_ENV != production`` alone is not enough — a hand-rolled
    deploy that forgets ``APP_ENV=production`` must not silently open billed
    endpoints.
    """
    expected = (settings.api_key or "").strip()
    if not expected:
        if settings.allow_unauthenticated:
            return
        raise ApiKeyNotConfiguredError()
    if not x_api_key or not compare_digest(x_api_key, expected):
        raise UnauthorizedError()


def get_clinic_repository(session: Session = Depends(get_db_session)) -> SqlAlchemyClinicRepository:
    return SqlAlchemyClinicRepository(session)


def get_signal_repository(session: Session = Depends(get_db_session)) -> SqlAlchemySignalRepository:
    return SqlAlchemySignalRepository(session)


def get_enrichment_repository(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyEnrichmentRepository:
    return SqlAlchemyEnrichmentRepository(session)


def get_score_repository(session: Session = Depends(get_db_session)) -> SqlAlchemyScoreRepository:
    return SqlAlchemyScoreRepository(session)


def get_scoring_config_repository(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyScoringConfigRepository:
    return SqlAlchemyScoringConfigRepository(session)


def get_website_crawler() -> Generator[HttpxWebsiteCrawler, None, None]:
    crawler = HttpxWebsiteCrawler(timeout=settings.crawler_timeout_seconds)
    try:
        yield crawler
    finally:
        crawler.close()


def get_clinic_source() -> Generator[GooglePlacesClient, None, None]:
    source = GooglePlacesClient(
        settings.google_places_api_key,
        max_pages=settings.places_max_pages,
    )
    try:
        yield source
    finally:
        source.close()


def get_discover_clinics(
    clinic_source: GooglePlacesClient = Depends(get_clinic_source),
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
) -> DiscoverClinics:
    return DiscoverClinics(clinic_source, clinic_repo)


def get_list_clinics(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
) -> ListClinics:
    return ListClinics(clinic_repo)


def get_get_clinic(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
) -> GetClinic:
    return GetClinic(clinic_repo)


def get_detect_signals(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    signal_repo: SqlAlchemySignalRepository = Depends(get_signal_repository),
    scoring_config_repo: SqlAlchemyScoringConfigRepository = Depends(get_scoring_config_repository),
    crawler: HttpxWebsiteCrawler = Depends(get_website_crawler),
) -> DetectSignals:
    return DetectSignals(clinic_repo, signal_repo, scoring_config_repo, crawler)


def get_list_clinic_signals(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    signal_repo: SqlAlchemySignalRepository = Depends(get_signal_repository),
) -> ListClinicSignals:
    return ListClinicSignals(clinic_repo, signal_repo)


def get_compute_score(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    signal_repo: SqlAlchemySignalRepository = Depends(get_signal_repository),
    score_repo: SqlAlchemyScoreRepository = Depends(get_score_repository),
    scoring_config_repo: SqlAlchemyScoringConfigRepository = Depends(get_scoring_config_repository),
) -> ComputeScore:
    return ComputeScore(clinic_repo, signal_repo, score_repo, scoring_config_repo)


def get_rescore_all(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    compute_score: ComputeScore = Depends(get_compute_score),
) -> RescoreAll:
    return RescoreAll(clinic_repo, compute_score)


def get_get_scoring_config(
    scoring_config_repo: SqlAlchemyScoringConfigRepository = Depends(get_scoring_config_repository),
) -> GetScoringConfig:
    return GetScoringConfig(scoring_config_repo)


def get_update_scoring_config(
    scoring_config_repo: SqlAlchemyScoringConfigRepository = Depends(get_scoring_config_repository),
    rescore_all: RescoreAll = Depends(get_rescore_all),
) -> UpdateScoringConfig:
    return UpdateScoringConfig(scoring_config_repo, rescore_all)


def get_detect_all_signals(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    detect_signals: DetectSignals = Depends(get_detect_signals),
) -> DetectAllSignals:
    return DetectAllSignals(clinic_repo, detect_signals)


def get_enrich_clinic(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    enrichment_repo: SqlAlchemyEnrichmentRepository = Depends(get_enrichment_repository),
    crawler: HttpxWebsiteCrawler = Depends(get_website_crawler),
) -> EnrichClinic:
    return EnrichClinic(clinic_repo, enrichment_repo, crawler)


def get_enrich_all_clinics(
    clinic_repo: SqlAlchemyClinicRepository = Depends(get_clinic_repository),
    enrich_clinic: EnrichClinic = Depends(get_enrich_clinic),
) -> EnrichAllClinics:
    return EnrichAllClinics(clinic_repo, enrich_clinic)
