import os
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config.settings import settings
from app.main import create_app
from app.presentation.middleware.rate_limit import RateLimitResult, RedisRateLimitStore


@pytest.fixture(autouse=True)
def _allow_unauthenticated_in_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the existing suite free of X-API-Key headers.

    Production defaults fail closed (empty API_KEY → 503). Tests opt into the
    explicit local escape hatch unless a case overrides it.
    """
    monkeypatch.setattr(settings, "allow_unauthenticated", True)
    monkeypatch.setattr(settings, "api_key", "")

    async def increment(self, key: str, window_seconds: int) -> RateLimitResult:
        counts = getattr(self, "_test_counts", {})
        counts[key] = counts.get(key, 0) + 1
        self._test_counts = counts
        return RateLimitResult(count=counts[key], retry_after_seconds=window_seconds)

    async def ping(self) -> None:
        return None

    async def close(self) -> None:
        return None

    monkeypatch.setattr(RedisRateLimitStore, "increment", increment)
    monkeypatch.setattr(RedisRateLimitStore, "ping", ping)
    monkeypatch.setattr(RedisRateLimitStore, "close", close)


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://dental_radar:dental_radar@localhost:5432/dental_radar_test",
    )


def _reset_database(database_url: str):
    eng = create_engine(database_url)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with eng.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()

    command.upgrade(alembic_cfg, "head")
    eng.dispose()
    return create_engine(database_url)


@pytest.fixture(scope="session")
def engine(database_url: str):
    eng = _reset_database(database_url)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from app.presentation.api.deps import get_db_session

    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def migrated_engine(engine):
    return engine


@pytest.fixture
def fake_source():
    from tests.support.fakes import FakeClinicSource

    return FakeClinicSource()


@pytest.fixture
def app_client(db_session, fake_source):
    from app.application.use_cases.discover_clinics import DiscoverClinics
    from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
    from app.presentation.api.deps import get_clinic_source, get_db_session, get_discover_clinics

    app = create_app()
    repo = SqlAlchemyClinicRepository(db_session)
    discover = DiscoverClinics(fake_source, repo)

    def override_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_clinic_source] = lambda: fake_source
    app.dependency_overrides[get_discover_clinics] = lambda: discover

    with TestClient(app) as test_client:
        yield test_client, fake_source, repo

    app.dependency_overrides.clear()
