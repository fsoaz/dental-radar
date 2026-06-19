from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.entities.scoring_config import ScoreBand, ScoringConfig
from app.domain.entities.signal import Signal
from app.domain.services.scoring_service import ScoringService
from app.domain.value_objects.priority import PriorityLevel
from app.domain.value_objects.signal_type import SignalType

SERVICE = ScoringService()

DEFAULT_CONFIG = ScoringConfig(
    version=1,
    active=True,
    weights={
        "HIRING": 25,
        "ADVERTISING": 30,
        "WEBSITE_QUALITY": 15,
        "MULTI_LOCATION": 40,
        "HIGH_TICKET": 20,
    },
    bands=[
        ScoreBand(name="COLD", min=0, max=50),
        ScoreBand(name="WARM", min=51, max=100),
        ScoreBand(name="HOT", min=101, max=150),
        ScoreBand(name="IMMEDIATE", min=151, max=None),
    ],
)


def _signal(signal_type: SignalType, weight: int | None = None) -> Signal:
    return Signal(
        id=uuid4(),
        clinic_id=uuid4(),
        type=signal_type,
        applied_weight=weight or 0,
        evidence="test",
        confidence=1.0,
        detected_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (50, PriorityLevel.COLD),
        (51, PriorityLevel.WARM),
        (100, PriorityLevel.WARM),
        (101, PriorityLevel.HOT),
        (150, PriorityLevel.HOT),
        (151, PriorityLevel.IMMEDIATE),
    ],
)
def test_priority_band_boundaries(total, expected):
    config = ScoringConfig(
        version=1,
        active=True,
        weights={"HIRING": total},
        bands=DEFAULT_CONFIG.bands,
    )
    signals = [_signal(SignalType.HIRING, total)]
    computed = SERVICE.compute(signals, config)
    assert computed.total == total
    assert computed.priority == expected


def test_breakdown_sums_to_total():
    signals = [
        _signal(SignalType.HIRING, 25),
        _signal(SignalType.ADVERTISING, 30),
    ]
    computed = SERVICE.compute(signals, DEFAULT_CONFIG)
    assert computed.total == 55
    assert sum(computed.breakdown.to_dict().values()) == computed.total


def test_config_weight_change_changes_score_without_code_change():
    signals = [_signal(SignalType.HIRING, 25)]
    low = SERVICE.compute(signals, DEFAULT_CONFIG)
    high_config = ScoringConfig(
        version=2,
        active=True,
        weights={"HIRING": 60},
        bands=DEFAULT_CONFIG.bands,
    )
    high = SERVICE.compute(signals, high_config)
    assert low.total == 25
    assert high.total == 60
