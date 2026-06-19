from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreBreakdown:
    points_by_type: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.points_by_type.values())

    def to_dict(self) -> dict[str, int]:
        return dict(self.points_by_type)

    @classmethod
    def from_signals(cls, signals, weights: dict[str, int]) -> "ScoreBreakdown":
        points: dict[str, int] = {}
        for signal in signals:
            signal_type = signal.type.value if hasattr(signal.type, "value") else str(signal.type)
            points[signal_type] = weights.get(signal_type, signal.applied_weight)
        return cls(points_by_type=points)

    def validate(self) -> None:
        if any(value < 0 for value in self.points_by_type.values()):
            raise ValueError("Breakdown points must be >= 0")
