from app.application.dto.clinic_dto import ClinicData
from app.application.dto.enrichment_dto import ClinicAIInput, EnrichmentResult, LLMCompletion
from app.application.dto.page_evidence import PageEvidence
from app.domain.value_objects.address import Address
from app.infrastructure.crawler.website_crawler import WebsiteFetchError, parse_page_evidence


class FakeClinicSource:
    def __init__(self, results: list[ClinicData] | None = None) -> None:
        self.results = list(results or [])
        self.queries: list[str] = []

    def search(self, query: str) -> list[ClinicData]:
        self.queries.append(query)
        return list(self.results)


class FakeWebsiteCrawler:
    def __init__(self, pages: dict[str, str] | None = None) -> None:
        self.pages = pages or {}
        self.fetched: list[str] = []
        self.failures: dict[str, str] = {}

    def set_page(self, url: str, html: str) -> None:
        self.pages[url] = html
        self.failures.pop(url, None)

    def fail(self, url: str, message: str = "DNS resolution failed") -> None:
        self.failures[url] = message

    def fetch(self, url: str) -> PageEvidence:
        self.fetched.append(url)
        if url in self.failures:
            raise WebsiteFetchError(url, self.failures[url])
        html = self.pages.get(url, self.pages.get("*", "<html></html>"))
        return parse_page_evidence(url, html)


DEFAULT_ENRICHMENT = EnrichmentResult(
    growth_probability=78,
    technology_maturity=65,
    marketing_sophistication=72,
    expansion_probability=80,
    explanation="Active implant marketing, modern site, two locations.",
)


class FakeLLMProvider:
    def __init__(
        self,
        result: EnrichmentResult | None = None,
        *,
        provider_name: str = "fake",
        model_name: str = "fake-model",
    ) -> None:
        self.result = result or DEFAULT_ENRICHMENT
        self.provider_name_value = provider_name
        self.model_name_value = model_name
        self.payloads: list[ClinicAIInput] = []

    @property
    def provider_name(self) -> str:
        return self.provider_name_value

    @property
    def model_name(self) -> str:
        return self.model_name_value

    def analyze_clinic(self, payload: ClinicAIInput) -> LLMCompletion:
        self.payloads.append(payload)
        return LLMCompletion(
            provider=self.provider_name,
            model=self.model_name,
            prompt_version="clinic_enrichment_v1",
            result=self.result,
        )


def make_clinic_data(
    *,
    place_id: str = "place-1",
    name: str = "Smile Dental",
    city: str = "Lisboa",
    state: str = "Lisboa",
    rating: float = 4.5,
    reviews: int = 100,
    website: str = "https://smile.example",
) -> ClinicData:
    return ClinicData(
        place_id=place_id,
        name=name,
        address=Address(
            street="Rua Example 1",
            city=city,
            state=state,
            postal_code="1000-001",
            country="Portugal",
        ),
        phone="+351210000000",
        website=website,
        google_rating=rating,
        google_review_count=reviews,
    )
