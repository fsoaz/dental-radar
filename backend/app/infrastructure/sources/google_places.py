import httpx

from app.application.dto.clinic_dto import ClinicData
from app.application.ports.clinic_source import ClinicSource
from app.domain.value_objects.address import Address

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
SEARCH_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.rating,places.userRatingCount,places.nationalPhoneNumber,"
    "places.websiteUri,places.addressComponents,nextPageToken"
)

COMPONENT_TYPE_MAP = {
    "street_number": "street_number",
    "route": "route",
    "locality": "city",
    "administrative_area_level_1": "state",
    "postal_code": "postal_code",
    "country": "country",
}


class GooglePlacesClient(ClinicSource):
    def __init__(
        self,
        api_key: str,
        *,
        client: httpx.Client | None = None,
        max_pages: int = 3,
    ) -> None:
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=30.0)
        self._max_pages = max(1, max_pages)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def search(self, query: str) -> list[ClinicData]:
        if not self._api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY is not configured")

        places: list[dict] = []
        page_token: str | None = None

        for _ in range(self._max_pages):
            body: dict = {"textQuery": query, "pageSize": 20}
            if page_token:
                body["pageToken"] = page_token

            response = self._client.post(
                PLACES_SEARCH_URL,
                headers={
                    "X-Goog-Api-Key": self._api_key,
                    "X-Goog-FieldMask": SEARCH_FIELD_MASK,
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            payload = response.json()
            places.extend(payload.get("places", []))
            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        return [self._map_place(place) for place in places]

    def _map_place(self, place: dict) -> ClinicData:
        place_id = place.get("id", "")
        if place_id.startswith("places/"):
            place_id = place_id.removeprefix("places/")

        display_name = place.get("displayName", {})
        name = display_name.get("text") if isinstance(display_name, dict) else str(display_name)

        location = place.get("location", {})
        address = self._parse_address(
            components=place.get("addressComponents", []),
            formatted=place.get("formattedAddress"),
            lat=location.get("latitude"),
            lng=location.get("longitude"),
        )

        return ClinicData(
            place_id=place_id,
            name=name or "Unknown Clinic",
            address=address,
            phone=place.get("nationalPhoneNumber"),
            website=place.get("websiteUri"),
            google_rating=place.get("rating"),
            google_review_count=place.get("userRatingCount") or 0,
            social_urls=[],
        )

    def _parse_address(
        self,
        *,
        components: list[dict],
        formatted: str | None,
        lat: float | None,
        lng: float | None,
    ) -> Address:
        parsed: dict[str, str] = {}
        street_parts: list[str] = []

        for component in components:
            for component_type in component.get("types", []):
                if component_type in ("street_number", "route"):
                    street_parts.append(component.get("longText", ""))
                elif component_type in COMPONENT_TYPE_MAP:
                    key = COMPONENT_TYPE_MAP[component_type]
                    parsed[key] = component.get("longText", "")

        street = " ".join(part for part in street_parts if part).strip() or formatted

        return Address(
            street=street,
            city=parsed.get("city"),
            state=parsed.get("state"),
            postal_code=parsed.get("postal_code"),
            country=parsed.get("country"),
            lat=lat,
            lng=lng,
        )
