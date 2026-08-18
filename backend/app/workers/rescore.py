import logging
import time

from sqlalchemy import text

from app.application.use_cases.compute_score import ComputeScore, RescoreAll
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.logging_config import configure_logging
from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
from app.infrastructure.repositories.sqlalchemy_rescore_job_repo import (
    SqlAlchemyRescoreJobRepository,
)
from app.infrastructure.repositories.sqlalchemy_score_repo import SqlAlchemyScoreRepository
from app.infrastructure.repositories.sqlalchemy_scoring_config_repo import (
    SqlAlchemyScoringConfigRepository,
)
from app.infrastructure.repositories.sqlalchemy_signal_repo import SqlAlchemySignalRepository

logger = logging.getLogger(__name__)
ADVISORY_LOCK_ID = 7_391_337


def _run_job() -> bool:
    with SessionLocal() as session:
        jobs = SqlAlchemyRescoreJobRepository(session)
        job = jobs.claim_next()
        if job is None:
            return False

        try:
            clinics = SqlAlchemyClinicRepository(session)
            configs = SqlAlchemyScoringConfigRepository(session)
            compute = ComputeScore(
                clinics,
                SqlAlchemySignalRepository(session),
                SqlAlchemyScoreRepository(session),
                configs,
            )
            config = configs.get_config(job.config_version)
            results = RescoreAll(clinics, compute).execute(commit_each=False, config=config)
            session.commit()
            jobs.succeed(job.id, len(results))
            logger.info(
                "Rescore job %s completed config_version=%s rescored=%s",
                job.id,
                job.config_version,
                len(results),
            )
        except Exception:
            session.rollback()
            logger.exception("Rescore job %s failed attempt=%s", job.id, job.attempts)
            jobs.fail(job.id)
        return True


def main() -> None:
    configure_logging()
    logger.info("Rescore worker starting")
    with engine.connect() as lock_connection:
        acquired = bool(
            lock_connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": ADVISORY_LOCK_ID}
            ).scalar_one()
        )
        if not acquired:
            logger.error("Another rescore worker holds the global worker lock; exiting")
            return

        with SessionLocal() as session:
            SqlAlchemyRescoreJobRepository(session).recover_running()

        try:
            while True:
                if not _run_job():
                    time.sleep(2)
        except KeyboardInterrupt:
            logger.info("Rescore worker stopping")
        finally:
            lock_connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": ADVISORY_LOCK_ID}
            )


if __name__ == "__main__":
    main()
