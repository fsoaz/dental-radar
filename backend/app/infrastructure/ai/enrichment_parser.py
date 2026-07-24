import hashlib
import json
import re
from pathlib import Path

from pydantic import ValidationError

from app.application.dto.enrichment_dto import ClinicAIInput, EnrichmentResult, SignalSummary

PROMPT_VERSION = "clinic_enrichment_v1"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class EnrichmentParseError(Exception):
    def __init__(self, message: str, raw: str | None = None) -> None:
        self.raw = raw
        super().__init__(message)


def load_prompt_template(version: str = PROMPT_VERSION) -> str:
    path = PROMPTS_DIR / f"{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def truncate_site_text(text: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "…"


def format_signals(signals: list[SignalSummary]) -> str:
    if not signals:
        return "none"
    parts = []
    for signal in signals:
        evidence = signal.evidence or "no evidence"
        parts.append(f"{signal.type}: {evidence}")
    return "; ".join(parts)


def build_user_prompt(payload: ClinicAIInput, max_site_text_chars: int) -> tuple[str, str]:
    template = load_prompt_template()
    if "USER:" not in template:
        raise ValueError("Prompt template must contain a USER: section")

    system_part, user_part = template.split("USER:", maxsplit=1)
    system_prompt = system_part.replace("SYSTEM:", "", 1).strip()
    user_template = user_part.strip()

    user_prompt = user_template.format(
        name=payload.name,
        site_text=truncate_site_text(payload.site_text, max_site_text_chars),
        signals=format_signals(payload.signals),
        rating=payload.rating if payload.rating is not None else "unknown",
        reviews=payload.reviews,
        locations_count=payload.locations_count,
    )
    return system_prompt, user_prompt


def compute_input_fingerprint(payload: ClinicAIInput, max_site_text_chars: int) -> str:
    data = {
        "name": payload.name,
        "site_text": truncate_site_text(payload.site_text, max_site_text_chars),
        "signals": sorted(f"{signal.type}:{signal.evidence or ''}" for signal in payload.signals),
        "rating": payload.rating,
        "reviews": payload.reviews,
        "locations_count": payload.locations_count,
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _extract_json(raw: str) -> object:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match is None:
            raise EnrichmentParseError("Response is not valid JSON", raw) from None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise EnrichmentParseError("Response is not valid JSON", raw) from exc


def parse_enrichment_response(raw: str) -> EnrichmentResult:
    payload = _extract_json(raw)
    if not isinstance(payload, dict):
        raise EnrichmentParseError("Response JSON must be an object", raw)

    try:
        return EnrichmentResult.model_validate(payload)
    except ValidationError as exc:
        raise EnrichmentParseError(str(exc), raw) from exc


REPAIR_USER_SUFFIX = """

Your previous response was invalid JSON or did not match the required schema.
Return ONLY corrected JSON with integer scores 0-100 and explanation <= 280 chars.
Previous response:
{previous}
"""
