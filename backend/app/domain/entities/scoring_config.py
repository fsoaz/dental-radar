from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreBand:
    name: str
    min: int
    max: int | None


@dataclass(frozen=True)
class ScoringConfig:
    version: int
    active: bool
    weights: dict[str, int]
    bands: list[ScoreBand]

    def priority_for_total(self, total: int) -> str:
        for band in self.bands:
            if total >= band.min and (band.max is None or total <= band.max):
                return band.name
        return self.bands[-1].name if self.bands else "COLD"
