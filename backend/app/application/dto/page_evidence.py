from dataclasses import dataclass


@dataclass(frozen=True)
class PageEvidence:
    url: str
    html: str
    text: str
    scripts: list[str]
    meta: dict[str, str]
    links: list[str]
