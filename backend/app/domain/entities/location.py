from dataclasses import dataclass
from uuid import UUID

from app.domain.value_objects.address import Address


@dataclass
class Location:
    id: UUID
    clinic_id: UUID
    address: Address
    is_primary: bool = False
