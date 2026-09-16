from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.enrichment_dto import EnrichmentResult, LLMCompletion
from app.application.use_cases.discover_clinics import DiscoverClinics
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
from app.infrastructure.repositories.sqlalchemy_score_repo import SqlAlchemyScoreRepository
from cli import _build_enrich_stack, main
from tests.support.fakes import FakeClinicSource, make_clinic_data


class _FakeProvider:
    provider_name = "gpt"
    model_name = "gpt-test"

    def analyze_clinic(self, payload):
        return LLMCompletion(
            provider=self.provider_name,
            model=self.model_name,
            prompt_version="clinic_enrichment_v1",
            result=EnrichmentResult(
                growth_probability=60,
                technology_maturity=70,
                marketing_sophistication=80,
                expansion_probability=50,
                explanation=f"Checked {payload.name}",
            ),
        )


def test_test_connection_command_returns_zero_on_success(monkeypatch, capsys):
    monkeypatch.setattr("cli.create_llm_provider", lambda: _FakeProvider())

    exit_code = main(["test-connection"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "=== Success! ===" in captured.out
    assert "Provider used: gpt" in captured.out


def test_test_connection_command_returns_one_on_failure(monkeypatch, capsys):
    def fail():
        raise RuntimeError("bad key")

    monkeypatch.setattr("cli.create_llm_provider", fail)

    exit_code = main(["test-connection"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Connection Failed" in captured.err
    assert "bad key" in captured.err


def test_score_all_requests_per_clinic_commits(monkeypatch, capsys):
    calls: list[bool] = []

    class _Session:
        def close(self) -> None:
            pass

    class _Batch:
        def execute(self, *, commit_each: bool):
            calls.append(commit_each)
            return []

    monkeypatch.setattr("cli.SessionLocal", _Session)
    monkeypatch.setattr("cli._build_score_stack", lambda _session: (object(), object(), _Batch()))

    assert main(["score", "--all"]) == 0
    assert calls == [True]
    assert "Scored 0 clinics" in capsys.readouterr().out


def test_score_all_persists_rows_after_command_session_closes(db_session, monkeypatch):
    clinic_repo = SqlAlchemyClinicRepository(db_session)
    DiscoverClinics(
        FakeClinicSource([make_clinic_data(place_id="cli-score-all")]),
        clinic_repo,
    ).execute("dentist")
    clinic = clinic_repo.list_clinics(ClinicListQuery()).items[0].clinic

    connection = db_session.connection()
    cli_session_factory = sessionmaker(bind=connection, expire_on_commit=False)
    monkeypatch.setattr("cli.SessionLocal", cli_session_factory)

    assert main(["score", "--all"]) == 0

    with Session(bind=connection) as verification_session:
        persisted = SqlAlchemyScoreRepository(verification_session).get_by_clinic(clinic.id)
        assert persisted is not None
        assert persisted.total == 0


def test_enrich_stack_defers_invalid_provider_validation(monkeypatch):
    monkeypatch.setattr("cli.settings.ai_provider", "bogus")

    _clinic_repo, _enrich, crawler, _batch = _build_enrich_stack(object())

    crawler.close()
