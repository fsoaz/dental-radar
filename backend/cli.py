import argparse
import sys
from uuid import UUID

from app.application.use_cases.compute_score import ComputeScore, RescoreAll
from app.application.use_cases.detect_all_signals import DetectAllSignals
from app.application.use_cases.detect_signals import DetectSignals
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.application.use_cases.enrich_clinic import EnrichAllClinics, EnrichClinic
from app.domain.services.signal_detection_service import SignalDetectionService
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


def _build_score_stack(session):
    clinic_repo = SqlAlchemyClinicRepository(session)
    signal_repo = SqlAlchemySignalRepository(session)
    score_repo = SqlAlchemyScoreRepository(session)
    scoring_repo = SqlAlchemyScoringConfigRepository(session)
    compute = ComputeScore(clinic_repo, signal_repo, score_repo, scoring_repo)
    return clinic_repo, compute, RescoreAll(clinic_repo, compute)


def run_discover(query: str) -> int:
    session = SessionLocal()
    try:
        repo = SqlAlchemyClinicRepository(session)
        source = GooglePlacesClient(
            settings.google_places_api_key,
            max_pages=settings.places_max_pages,
        )
        use_case = DiscoverClinics(source, repo)
        result = use_case.execute(query)
        print(
            f"Ingested {result.ingested} clinics "
            f"({result.created} created, {result.updated} updated)"
        )
        return 0
    finally:
        session.close()


def run_detect(clinic_id: UUID | None, detect_all: bool) -> int:
    session = SessionLocal()
    crawler = HttpxWebsiteCrawler(timeout=settings.crawler_timeout_seconds)
    try:
        clinic_repo = SqlAlchemyClinicRepository(session)
        signal_repo = SqlAlchemySignalRepository(session)
        scoring_repo = SqlAlchemyScoringConfigRepository(session)
        detect_use_case = DetectSignals(
            clinic_repo,
            signal_repo,
            scoring_repo,
            crawler,
            SignalDetectionService(),
        )

        if detect_all:
            detect_all_use_case = DetectAllSignals(clinic_repo, detect_use_case)
            results = detect_all_use_case.execute()
            total = sum(count for _, count in results)
            print(f"Detected {total} signals across {len(results)} clinics")
            return 0

        if clinic_id is None:
            print("Provide --clinic-id or --all", file=sys.stderr)
            return 1

        result = detect_use_case.execute(clinic_id)
        print(f"Detected {result.detected} signals for clinic {clinic_id}")
        if result.skip_reason:
            print(f"Note: {result.skip_reason}")
        return 0
    finally:
        crawler.close()
        session.close()


def _build_enrich_stack(session):
    clinic_repo = SqlAlchemyClinicRepository(session)
    enrichment_repo = SqlAlchemyEnrichmentRepository(session)
    crawler = HttpxWebsiteCrawler(timeout=settings.crawler_timeout_seconds)
    enrich = EnrichClinic(clinic_repo, enrichment_repo, crawler)
    return clinic_repo, enrich, crawler, EnrichAllClinics(clinic_repo, enrich)


def run_score(clinic_id: UUID | None, score_all: bool) -> int:
    session = SessionLocal()
    try:
        _clinic_repo, compute, rescore_all = _build_score_stack(session)
        if score_all:
            results = rescore_all.execute()
            print(f"Scored {len(results)} clinics")
            return 0
        if clinic_id is None:
            print("Provide --clinic-id or --all", file=sys.stderr)
            return 1
        result = compute.execute(clinic_id)
        print(
            f"Clinic {clinic_id} scored {result.total} ({result.priority}) "
            f"using config v{result.config_version}"
        )
        return 0
    finally:
        session.close()


def run_enrich(clinic_id: UUID | None, enrich_all: bool, force: bool) -> int:
    session = SessionLocal()
    try:
        _clinic_repo, enrich, crawler, enrich_all_use_case = _build_enrich_stack(session)
        if enrich_all:
            results = enrich_all_use_case.execute(force=force)
            enriched = sum(1 for result in results if not result.skipped)
            skipped = sum(1 for result in results if result.skipped)
            print(f"Enriched {enriched} clinics ({skipped} skipped unchanged)")
            return 0
        if clinic_id is None:
            print("Provide --clinic-id or --all", file=sys.stderr)
            return 1
        result = enrich.execute(clinic_id, force=force)
        if result.skipped:
            print(f"Skipped clinic {clinic_id}: {result.skip_reason}")
        else:
            print(
                f"Clinic {clinic_id} enriched "
                f"(growth={result.growth_probability}, provider={result.provider})"
            )
        return 0
    finally:
        if "crawler" in locals():
            crawler.close()
        session.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dental-radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover_parser = subparsers.add_parser(
        "discover",
        help="Discover clinics from Google Places",
    )
    discover_parser.add_argument(
        "--query",
        required=True,
        help='Search query, e.g. "dentist in Lisbon"',
    )

    detect_parser = subparsers.add_parser("detect", help="Detect buying signals for clinics")
    detect_group = detect_parser.add_mutually_exclusive_group(required=True)
    detect_group.add_argument("--clinic-id", type=UUID)
    detect_group.add_argument("--all", action="store_true")

    score_parser = subparsers.add_parser("score", help="Compute clinic scores")
    score_group = score_parser.add_mutually_exclusive_group(required=True)
    score_group.add_argument("--clinic-id", type=UUID)
    score_group.add_argument("--all", action="store_true")

    enrich_parser = subparsers.add_parser("enrich", help="Run AI enrichment for clinics")
    enrich_group = enrich_parser.add_mutually_exclusive_group(required=True)
    enrich_group.add_argument("--clinic-id", type=UUID)
    enrich_group.add_argument("--all", action="store_true")
    enrich_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-enrich even when inputs are unchanged",
    )

    args = parser.parse_args(argv)

    if args.command == "discover":
        return run_discover(args.query)
    if args.command == "detect":
        return run_detect(args.clinic_id, args.all)
    if args.command == "score":
        return run_score(args.clinic_id, args.all)
    if args.command == "enrich":
        return run_enrich(args.clinic_id, args.all, args.force)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
