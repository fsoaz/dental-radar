from app.domain.entities.clinic import Clinic
from app.domain.entities.location import Location
from app.domain.value_objects.address import Address
from app.infrastructure.db.models import ClinicModel, LocationModel


def clinic_model_to_entity(model: ClinicModel) -> Clinic:
    return Clinic(
        id=model.id,
        place_id=model.place_id,
        name=model.name,
        phone=model.phone,
        website=model.website,
        google_rating=float(model.google_rating) if model.google_rating is not None else None,
        google_review_count=model.google_review_count,
        locations_count=model.locations_count,
        social_urls=list(model.social_urls or []),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def location_model_to_entity(model: LocationModel) -> Location:
    return Location(
        id=model.id,
        clinic_id=model.clinic_id,
        address=Address(
            street=model.street,
            city=model.city,
            state=model.state,
            postal_code=model.postal_code,
            country=model.country,
            lat=float(model.lat) if model.lat is not None else None,
            lng=float(model.lng) if model.lng is not None else None,
        ),
        is_primary=model.is_primary,
    )


def apply_clinic_entity(model: ClinicModel, clinic: Clinic) -> None:
    model.name = clinic.name
    model.phone = clinic.phone
    model.website = clinic.website
    model.google_rating = clinic.google_rating
    model.google_review_count = clinic.google_review_count
    model.social_urls = list(clinic.social_urls)


def apply_location_entity(model: LocationModel, location: Location) -> None:
    model.street = location.address.street
    model.city = location.address.city
    model.state = location.address.state
    model.postal_code = location.address.postal_code
    model.country = location.address.country
    model.lat = location.address.lat
    model.lng = location.address.lng
    model.is_primary = location.is_primary
