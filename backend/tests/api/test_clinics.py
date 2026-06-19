from uuid import uuid4

from app.application.use_cases.discover_clinics import DiscoverClinics
from app.domain.repositories.clinic_repo import ClinicListQuery
from app.infrastructure.repositories.sqlalchemy_clinic_repo import SqlAlchemyClinicRepository
from app.infrastructure.sources.google_places import GooglePlacesClient
from tests.support.fakes import FakeClinicSource, make_clinic_data


def test_discover_upserts_by_place_id(db_session):
    repo = SqlAlchemyClinicRepository(db_session)
    source = FakeClinicSource([make_clinic_data(place_id="abc123", reviews=50)])
    use_case = DiscoverClinics(source, repo)

    first = use_case.execute("dentist in Lisbon")
    assert first.ingested == 1
    assert first.created == 1
    assert first.updated == 0

    source.results = [make_clinic_data(place_id="abc123", reviews=75, rating=4.8)]
    second = use_case.execute("dentist in Lisbon")
    assert second.created == 0
    assert second.updated == 1

    listed = repo.list_clinics(ClinicListQuery())
    assert listed.total == 1
    assert listed.items[0].clinic.google_review_count == 75
    assert listed.items[0].clinic.google_rating == 4.8


def test_discover_endpoint_returns_counts(app_client):
    client, source, _repo = app_client
    source.results = [
        make_clinic_data(place_id="p1"),
        make_clinic_data(place_id="p2", name="Second Clinic"),
    ]

    response = client.post("/api/v1/clinics/discover", json={"query": "dentist in Lisbon"})
    assert response.status_code == 202
    assert response.json() == {"ingested": 2, "created": 2, "updated": 0}


def test_list_clinics_pagination(app_client):
    client, _source, repo = app_client
    for index in range(25):
        DiscoverClinics(
            FakeClinicSource([make_clinic_data(place_id=f"page-{index}", name=f"Clinic {index}")]),
            repo,
        ).execute("dentist")

    page_one = client.get("/api/v1/clinics?page=1&page_size=20")
    assert page_one.status_code == 200
    body = page_one.json()
    assert len(body["data"]) == 20
    assert body["total"] == 25

    page_two = client.get("/api/v1/clinics?page=2&page_size=20")
    assert len(page_two.json()["data"]) == 5


def test_list_clinics_filters_by_q_and_state(app_client):
    client, _source, repo = app_client
    DiscoverClinics(
        FakeClinicSource([make_clinic_data(place_id="lisboa-1", city="Lisboa", state="Lisboa")]),
        repo,
    ).execute("dentist")
    DiscoverClinics(
        FakeClinicSource(
            [make_clinic_data(place_id="porto-1", name="Porto Care", city="Porto", state="Porto")]
        ),
        repo,
    ).execute("dentist")

    filtered = client.get("/api/v1/clinics?state=Porto")
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1
    assert filtered.json()["data"][0]["name"] == "Porto Care"


def test_get_clinic_detail(app_client):
    client, source, repo = app_client
    source.results = [make_clinic_data(place_id="detail-1")]
    client.post("/api/v1/clinics/discover", json={"query": "dentist"})
    clinic_id = repo.list_clinics(ClinicListQuery()).items[0].clinic.id

    response = client.get(f"/api/v1/clinics/{clinic_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Smile Dental"
    assert body["place_id"] == "detail-1"
    assert body["address"]["city"] == "Lisboa"
    assert body["signals"] == []
    assert body["score"] is None
    assert body["enrichment"] is None


def test_get_clinic_not_found(client):
    response = client.get(f"/api/v1/clinics/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CLINIC_NOT_FOUND"


class _FakeHttpClient:
    def post(self, url, headers=None, json=None):
        return _FakeResponse(
            {
                "places": [
                    {
                        "id": "places/ChIJ123",
                        "displayName": {"text": "Lisboa Dental"},
                        "formattedAddress": "Rua A, Lisboa",
                        "location": {"latitude": 38.7, "longitude": -9.1},
                        "rating": 4.6,
                        "userRatingCount": 42,
                        "nationalPhoneNumber": "+351210000000",
                        "websiteUri": "https://lisboa-dental.example",
                        "addressComponents": [
                            {"longText": "Lisboa", "types": ["locality"]},
                            {"longText": "Lisboa", "types": ["administrative_area_level_1"]},
                        ],
                    }
                ]
            }
        )


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_google_places_maps_response():
    client = GooglePlacesClient(api_key="test-key", client=_FakeHttpClient())
    results = client.search("dentist in Lisbon")

    assert len(results) == 1
    assert results[0].place_id == "ChIJ123"
    assert results[0].name == "Lisboa Dental"
    assert results[0].google_review_count == 42
    assert results[0].address.city == "Lisboa"
