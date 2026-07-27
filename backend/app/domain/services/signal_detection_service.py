import re
from dataclasses import dataclass

from app.application.dto.page_evidence import PageEvidence
from app.domain.value_objects.signal_type import SignalType


@dataclass(frozen=True)
class DetectedSignal:
    signal_type: SignalType
    evidence: str
    confidence: float
    locations_count: int | None = None


HIRING_KEYWORDS = (
    "implantologist",
    "orthodontist",
    "receptionist",
    "sales coordinator",
    "we are hiring",
    "join our team",
    "careers",
    "job opening",
    # Portuguese (Lisbon pilot)
    "estamos a recrutar",
    "recrutamento",
    "carreiras",
    "junta-te à equipa",
    "junta-te a nossa equipa",
    "vaga de emprego",
    "oferta de emprego",
)

ADVERTISING_MARKERS = (
    "fbq(",
    "facebook.com/tr",
    "googletagmanager.com",
    "gtag(",
    "googleadservices.com",
    "google_conversion",
    "aw-",
)

QUALITY_MARKERS = (
    'name="viewport"',
    'content="width=device-width',
    "<form",
    "calendly.com",
    "localmed.com",
    "nexhealth",
    "online scheduling",
    "book appointment",
    "marcar consulta",
    "agendar consulta",
)

HIGH_TICKET_KEYWORDS = (
    "dental implant",
    "implants",
    "invisalign",
    "clear aligner",
    "cosmetic dentistry",
    "veneers",
    "oral rehabilitation",
    "oral rehab",
    # Portuguese
    "implantes",
    "implante dentário",
    "implante dentario",
    "facetas",
    "facetas dentárias",
    "facetas dentarias",
    "alinhadores",
    "alinhadores invisíveis",
    "alinhadores invisiveis",
    "ortodontia",
    "reabilitação oral",
    "reabilitacao oral",
)

MULTI_LOCATION_MARKERS = (
    "our locations",
    "multiple locations",
    "branch office",
    "find a location",
    "location 1",
    "location 2",
    "as nossas clínicas",
    "as nossas clinicas",
    "várias localizações",
    "varias localizacoes",
    "outras clínicas",
    "outras clinicas",
)


class SignalDetectionService:
    def _build_haystack(self, evidence: PageEvidence) -> str:
        return " ".join(
            [
                evidence.text,
                evidence.html,
                " ".join(evidence.scripts),
                " ".join(evidence.links),
            ]
        ).lower()

    def estimate_locations_count(self, evidence: PageEvidence) -> int:
        """Best-guess location count from current evidence, always computed fresh.

        Unlike the MULTI_LOCATION signal (only emitted when evidence clears a
        confidence threshold), this always reflects the latest crawl so a
        clinic's stored count can go back down after it drops below that bar.
        """
        return self._estimate_locations_count(self._build_haystack(evidence), evidence)

    def detect(self, evidence: PageEvidence) -> list[DetectedSignal]:
        haystack = self._build_haystack(evidence)

        detected: list[DetectedSignal] = []

        for detector in (
            self._detect_hiring,
            self._detect_advertising,
            self._detect_website_quality,
            self._detect_multi_location,
            self._detect_high_ticket,
        ):
            result = detector(haystack, evidence)
            if result is not None:
                detected.append(result)

        return detected

    def _detect_hiring(self, haystack: str, evidence: PageEvidence) -> DetectedSignal | None:
        for keyword in HIRING_KEYWORDS:
            if keyword in haystack:
                return DetectedSignal(
                    signal_type=SignalType.HIRING,
                    evidence=f"Found hiring keyword '{keyword}' on {evidence.url}",
                    confidence=0.85,
                )
        if any(
            "career" in link or "jobs" in link or "carreira" in link or "emprego" in link
            for link in evidence.links
        ):
            return DetectedSignal(
                signal_type=SignalType.HIRING,
                evidence=f"Found careers/jobs link on {evidence.url}",
                confidence=0.9,
            )
        return None

    def _detect_advertising(self, haystack: str, evidence: PageEvidence) -> DetectedSignal | None:
        for marker in ADVERTISING_MARKERS:
            if marker.lower() in haystack:
                return DetectedSignal(
                    signal_type=SignalType.ADVERTISING,
                    evidence=f"Found advertising marker '{marker}' on {evidence.url}",
                    confidence=0.9,
                )
        return None

    def _detect_website_quality(
        self, haystack: str, evidence: PageEvidence
    ) -> DetectedSignal | None:
        matches = [marker for marker in QUALITY_MARKERS if marker.lower() in haystack]
        if len(matches) >= 2:
            return DetectedSignal(
                signal_type=SignalType.WEBSITE_QUALITY,
                evidence=f"Modern site markers: {', '.join(matches[:3])}",
                confidence=min(0.7 + 0.1 * len(matches), 1.0),
            )
        return None

    def _estimate_locations_count(self, haystack: str, evidence: PageEvidence) -> int:
        branch_links = [
            link
            for link in evidence.links
            if any(
                token in link.lower()
                for token in ("location", "branch", "office", "clinica", "clínica", "localiza")
            )
        ]
        marker_hits = sum(1 for marker in MULTI_LOCATION_MARKERS if marker in haystack)
        # US ZIP (12345 or 12345-6789) and Portuguese postal codes (1000-001).
        us_zips = len(re.findall(r"\b\d{5}(?:-\d{4})?\b", evidence.text))
        pt_postals = len(re.findall(r"\b\d{4}-\d{3}\b", evidence.text))
        address_count = max(us_zips, pt_postals)

        return max(
            1,
            len(branch_links) if len(branch_links) >= 2 else 0,
            marker_hits + 1 if marker_hits >= 2 else 0,
            2 if address_count >= 2 else 0,
        )

    def _detect_multi_location(
        self, haystack: str, evidence: PageEvidence
    ) -> DetectedSignal | None:
        locations_count = self._estimate_locations_count(haystack, evidence)

        if locations_count >= 2:
            return DetectedSignal(
                signal_type=SignalType.MULTI_LOCATION,
                evidence=f"Detected {locations_count} locations/branches on {evidence.url}",
                confidence=0.85,
                locations_count=locations_count,
            )
        return None

    def _detect_high_ticket(self, haystack: str, evidence: PageEvidence) -> DetectedSignal | None:
        matched = [keyword for keyword in HIGH_TICKET_KEYWORDS if keyword in haystack]
        if matched:
            return DetectedSignal(
                signal_type=SignalType.HIGH_TICKET,
                evidence=f"High-ticket services mentioned: {', '.join(matched[:3])}",
                confidence=min(0.75 + 0.05 * len(matched), 1.0),
            )
        return None
