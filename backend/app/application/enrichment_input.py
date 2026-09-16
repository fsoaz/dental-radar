import hashlib
import json
import re

from app.application.dto.enrichment_dto import ClinicAIInput


def normalize_site_text(text: str, max_chars: int) -> str:
    """Normalize and truncate site text exactly as it is sent to LLM providers."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "…"


def compute_input_fingerprint(payload: ClinicAIInput, max_site_text_chars: int) -> str:
    data = {
        "name": payload.name,
        "site_text": normalize_site_text(payload.site_text, max_site_text_chars),
        "signals": sorted(f"{signal.type}:{signal.evidence or ''}" for signal in payload.signals),
        "rating": payload.rating,
        "reviews": payload.reviews,
        "locations_count": payload.locations_count,
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
