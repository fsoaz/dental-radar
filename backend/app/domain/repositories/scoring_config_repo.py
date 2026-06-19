from typing import Protocol

from app.domain.entities.scoring_config import ScoringConfig


class ScoringConfigRepository(Protocol):
    def get_active_weights(self) -> dict[str, int]:
        """Return signal type -> weight mapping from the active config."""

    def get_active_config(self) -> ScoringConfig:
        """Return the full active scoring configuration."""

    def update_active_config(
        self,
        *,
        weights: dict[str, int],
        bands: list[dict],
    ) -> ScoringConfig:
        """Create a new config version and mark it active."""
