from app.application.dto.enrichment_dto import EnrichmentResult, LLMCompletion
from cli import main


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
