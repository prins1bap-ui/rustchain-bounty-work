import httpx
import pytest

from src.scanner import audit_url, deduplicate_urls, normalize_url, parse_html, validate_public_url


def test_parse_html_extracts_expected_signals():
    html = """
    <html lang="en"><head>
      <title>Acme Widgets</title>
      <meta name="description" content="Industrial widgets and service">
      <meta name="generator" content="WordPress 6.8">
      <link rel="canonical" href="/home">
      <script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC123"></script>
      <script src="https://js.stripe.com/v3/"></script>
      <script type="application/ld+json">
        {"@type":"Organization","name":"Acme Industries","email":"info@acme.test","telephone":"+1 616 555 0123","sameAs":["https://www.linkedin.com/company/acme"]}
      </script>
    </head><body>
      <form action="/contact"><input name="email"></form>
      <a href="mailto:sales@acme.test?subject=hello">Email us</a>
      <a href="tel:+16165550100">Call us</a>
      <a href="https://instagram.com/acme">Instagram</a>
      <a href="https://www.facebook.com/sharer/sharer.php?u=x">Do not capture share</a>
      <p>Call (616) 555-0100</p>
      <script>fake@sentry.io; 616-555-9999</script>
    </body></html>
    """
    result = parse_html(html, base_url="https://acme.test/path")
    assert result["title"] == "Acme Widgets"
    assert result["metaDescription"] == "Industrial widgets and service"
    assert result["generator"] == "WordPress 6.8"
    assert result["language"] == "en"
    assert result["canonicalUrl"] == "https://acme.test/home"
    assert result["organizationName"] == "Acme Industries"
    assert result["structuredDataTypes"] == ["Organization"]
    assert result["forms"] == 1
    assert result["emails"] == ["info@acme.test", "sales@acme.test"]
    assert "+16165550100" in result["phones"]
    assert "+16165550123" in result["phones"]
    assert "(616) 555-0100" in result["phones"]
    assert result["socialProfiles"]["linkedin"] == ["https://www.linkedin.com/company/acme"]
    assert result["socialProfiles"]["instagram"] == ["https://instagram.com/acme"]
    assert "facebook" not in result["socialProfiles"]
    assert "Google Tag Manager" in result["detectedTechnologies"]
    assert "Stripe" in result["detectedTechnologies"]
    assert "WordPress" in result["detectedTechnologies"]


def test_normalize_and_deduplicate():
    assert normalize_url("Example.com") == "https://example.com/"
    urls, duplicates = deduplicate_urls(["example.com", "https://example.com/", "https://example.com/a"])
    assert urls == ["example.com", "https://example.com/a"]
    assert duplicates == 1


@pytest.mark.parametrize("url", [
    "http://127.0.0.1",
    "http://10.0.0.1",
    "http://169.254.169.254/latest/meta-data",
    "http://[::1]/",
])
def test_private_ip_targets_blocked_without_dns(url):
    with pytest.raises(ValueError):
        validate_public_url(url, resolve_dns=False)


def test_nonstandard_port_rejected():
    result = audit_url("https://example.com:8443")
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "INVALID_URL"


def test_invalid_scheme_returns_error():
    result = audit_url("file:///etc/passwd")
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "INVALID_URL"


def test_dns_resolution_error_is_distinct(monkeypatch):
    def fail_dns(host, port, proto=None):
        import socket
        raise socket.gaierror("not found")

    monkeypatch.setattr("src.scanner.socket.getaddrinfo", fail_dns)
    result = audit_url("definitely-not-real.invalid")
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "DNS_ERROR"


def _mock_client_factory(handler):
    def factory(*args, **kwargs):
        kwargs.pop("event_hooks", None)
        kwargs["transport"] = httpx.MockTransport(handler)
        return httpx.Client(*args, **kwargs)
    return factory


def test_success_and_output_contract(monkeypatch):
    monkeypatch.setattr("src.scanner.validate_public_url", lambda url, resolve_dns=True: normalize_url(url))

    def handler(request):
        return httpx.Response(
            200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "server": "unit-test",
                "strict-transport-security": "max-age=31536000",
                "x-content-type-options": "nosniff",
            },
            text="<html><head><title>Shop</title></head><body><script src='https://cdn.shopify.com/a.js'></script><form></form></body></html>",
            request=request,
        )

    result = audit_url("shop.test", client_factory=_mock_client_factory(handler))
    assert result["status"] == "SUCCESS"
    assert result["statusCode"] == 200
    assert result["title"] == "Shop"
    assert result["forms"] == 1
    assert result["detectedTechnologies"] == ["Shopify"]
    assert result["errorCode"] is None
    assert result["bytesRead"] > 0
    assert "strict-transport-security" in result["securityHeadersPresent"]
    assert "content-security-policy" in result["securityHeadersMissing"]


def test_http_error_is_structured_and_not_parsed(monkeypatch):
    monkeypatch.setattr("src.scanner.validate_public_url", lambda url, resolve_dns=True: normalize_url(url))

    def handler(request):
        return httpx.Response(404, headers={"content-type": "text/html"}, text="not found", request=request)

    result = audit_url("missing.test", client_factory=_mock_client_factory(handler))
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "HTTP_404"
    assert result["detectedTechnologies"] == []


def test_non_html_error(monkeypatch):
    monkeypatch.setattr("src.scanner.validate_public_url", lambda url, resolve_dns=True: normalize_url(url))

    def handler(request):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF", request=request)

    result = audit_url("pdf.test", client_factory=_mock_client_factory(handler))
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "UNSUPPORTED_CONTENT_TYPE"


def test_transient_status_retries_once(monkeypatch):
    monkeypatch.setattr("src.scanner.validate_public_url", lambda url, resolve_dns=True: normalize_url(url))
    monkeypatch.setattr("src.scanner.time.sleep", lambda _: None)
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(503, headers={"content-type": "text/html"}, text="busy", request=request)
        return httpx.Response(200, headers={"content-type": "text/html"}, text="<title>Recovered</title>", request=request)

    result = audit_url("retry.test", max_retries=1, client_factory=_mock_client_factory(handler))
    assert calls["count"] == 2
    assert result["status"] == "SUCCESS"
    assert result["title"] == "Recovered"
