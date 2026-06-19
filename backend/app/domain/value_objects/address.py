from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    lat: float | None = None
    lng: float | None = None

    @property
    def formatted(self) -> str | None:
        parts = [self.street, self.city, self.state, self.postal_code, self.country]
        cleaned = [part for part in parts if part]
        return ", ".join(cleaned) if cleaned else None
