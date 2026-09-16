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
