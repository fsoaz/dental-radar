from dataclasses import dataclass


@dataclass(frozen=True)
class PageEvidence:
    url: str
    html: str
    text: str
    scripts: list[str]
    links: list[str]
