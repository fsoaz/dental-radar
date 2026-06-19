from app.domain.services.signal_detection_service import SignalDetectionService
from app.infrastructure.crawler.website_crawler import parse_page_evidence

SERVICE = SignalDetectionService()


def _evidence(html: str, url: str = "https://clinic.example"):
    return parse_page_evidence(url, html)


def test_hiring_detector_fires_on_careers_keyword():
    result = SERVICE.detect(_evidence("<html><body>We are hiring an implantologist</body></html>"))
    types = {item.signal_type.value for item in result}
    assert "HIRING" in types


def test_hiring_detector_ignores_unrelated_html():
    html = "<html><body>Welcome to our family dental practice</body></html>"
    result = SERVICE.detect(_evidence(html))
    types = {item.signal_type.value for item in result}
    assert "HIRING" not in types


def test_advertising_detector_fires_on_meta_pixel():
    html = "<html><script>fbq('init', '123');</script></html>"
    result = SERVICE.detect(_evidence(html))
    assert any(item.signal_type.value == "ADVERTISING" for item in result)


def test_website_quality_detector_requires_multiple_markers():
    weak = _evidence("<html><body><p>Welcome to our clinic</p></body></html>")
    strong = _evidence(
        """
        <html>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <form><input type="email"><button>Book appointment</button></form>
        </html>
        """
    )
    assert not any(item.signal_type.value == "WEBSITE_QUALITY" for item in SERVICE.detect(weak))
    assert any(item.signal_type.value == "WEBSITE_QUALITY" for item in SERVICE.detect(strong))


def test_multi_location_detector_fires_on_branch_links():
    html = """
    <html><body>
      Our locations across the city.
      <a href="/location/lisboa">Lisboa branch office</a>
      <a href="/location/porto">Porto branch office</a>
    </body></html>
    """
    result = SERVICE.detect(_evidence(html))
    multi = next(item for item in result if item.signal_type.value == "MULTI_LOCATION")
    assert multi.locations_count >= 2


def test_high_ticket_detector_fires_on_implants():
    html = "<html><body>Specialists in dental implants and veneers</body></html>"
    result = SERVICE.detect(_evidence(html))
    assert any(item.signal_type.value == "HIGH_TICKET" for item in result)


def test_detected_signals_include_evidence():
    result = SERVICE.detect(_evidence("<html><body>We are hiring an orthodontist</body></html>"))
    assert result[0].evidence
