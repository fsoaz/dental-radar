from dataclasses import dataclass


@dataclass(frozen=True)
class SignalWeight:
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Signal weight must be >= 0")
