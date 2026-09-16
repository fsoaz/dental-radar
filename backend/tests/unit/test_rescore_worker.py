from types import SimpleNamespace
from uuid import uuid4

from app.workers import rescore


class _Session:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        pass

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class _Jobs:
    def __init__(self, _session) -> None:
        self.job = SimpleNamespace(id=uuid4(), config_version=2, attempts=1)
        self.succeeded: tuple[object, int] | None = None
        self.failed: object | None = None

    def claim_next(self):
        return self.job

    def succeed(self, job_id, rescored: int) -> None:
        self.succeeded = (job_id, rescored)

    def fail(self, job_id) -> None:
        self.failed = job_id


class _Configs:
    def __init__(self, _session) -> None:
        pass

    def get_config(self, version: int):
        return SimpleNamespace(version=version)


def _wire_worker(monkeypatch, session: _Session, batch_type) -> _Jobs:
    jobs = _Jobs(session)
    monkeypatch.setattr(rescore, "SessionLocal", lambda: session)
    monkeypatch.setattr(rescore, "SqlAlchemyRescoreJobRepository", lambda _session: jobs)
    monkeypatch.setattr(rescore, "SqlAlchemyClinicRepository", lambda _session: object())
    monkeypatch.setattr(rescore, "SqlAlchemyScoringConfigRepository", _Configs)
    monkeypatch.setattr(rescore, "SqlAlchemySignalRepository", lambda _session: object())
    monkeypatch.setattr(rescore, "SqlAlchemyScoreRepository", lambda _session: object())
    monkeypatch.setattr(rescore, "ComputeScore", lambda *_args: object())
    monkeypatch.setattr(rescore, "RescoreAll", batch_type)
    return jobs


def test_worker_rescores_in_one_caller_owned_transaction(monkeypatch) -> None:
    session = _Session()

    class _Batch:
        def __init__(self, *_args) -> None:
            pass

        def execute(self, *, commit_each: bool, config):
            assert commit_each is False
            assert config.version == 2
            return [object(), object()]

    jobs = _wire_worker(monkeypatch, session, _Batch)

    assert rescore._run_job() is True
    assert session.commits == 1
    assert session.rollbacks == 0
    assert jobs.succeeded == (jobs.job.id, 2)


def test_worker_rolls_back_batch_when_rescoring_fails(monkeypatch) -> None:
    session = _Session()

    class _FailingBatch:
        def __init__(self, *_args) -> None:
            pass

        def execute(self, *, commit_each: bool, config):
            assert commit_each is False
            raise RuntimeError("score failed")

    jobs = _wire_worker(monkeypatch, session, _FailingBatch)

    assert rescore._run_job() is True
    assert session.commits == 0
    assert session.rollbacks == 1
    assert jobs.failed == jobs.job.id
