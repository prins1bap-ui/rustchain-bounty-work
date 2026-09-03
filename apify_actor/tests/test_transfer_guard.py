import httpx

from src.scanner import audit_url, normalize_url


class _ExplodingStream(httpx.SyncByteStream):
    """Fails if a response body is consumed when headers already prove it unbillable."""

    def __iter__(self):
        raise AssertionError("Uncharged response body must not be downloaded")


def _mock_client_factory(handler):
    def factory(*args, **kwargs):
        kwargs.pop("event_hooks", None)
        kwargs["transport"] = httpx.MockTransport(handler)
        return httpx.Client(*args, **kwargs)

    return factory


def _disable_real_dns(monkeypatch):
    monkeypatch.setattr(
        "src.scanner.validate_public_url",
        lambda url, resolve_dns=True: normalize_url(url),
    )


def test_http_error_body_is_not_downloaded(monkeypatch):
    _disable_real_dns(monkeypatch)

    def handler(request):
        return httpx.Response(
            404,
            headers={"content-type": "text/html"},
            stream=_ExplodingStream(),
            request=request,
        )

    result = audit_url("missing.test", client_factory=_mock_client_factory(handler))
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "HTTP_404"
    assert result["bytesRead"] == 0


def test_non_html_body_is_not_downloaded(monkeypatch):
    _disable_real_dns(monkeypatch)

    def handler(request):
        return httpx.Response(
            200,
            headers={"content-type": "application/pdf"},
            stream=_ExplodingStream(),
            request=request,
        )

    result = audit_url("document.test", client_factory=_mock_client_factory(handler))
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "UNSUPPORTED_CONTENT_TYPE"
    assert result["bytesRead"] == 0


def test_missing_content_type_body_is_not_downloaded(monkeypatch):
    _disable_real_dns(monkeypatch)

    def handler(request):
        return httpx.Response(200, stream=_ExplodingStream(), request=request)

    result = audit_url("ambiguous.test", client_factory=_mock_client_factory(handler))
    assert result["status"] == "ERROR"
    assert result["errorCode"] == "UNVERIFIED_CONTENT_TYPE"
    assert result["bytesRead"] == 0


def test_transient_retry_does_not_consume_failed_body(monkeypatch):
    _disable_real_dns(monkeypatch)
    monkeypatch.setattr("src.scanner.time.sleep", lambda _: None)
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(
                503,
                headers={"content-type": "text/html"},
                stream=_ExplodingStream(),
                request=request,
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text="<html><title>Recovered</title></html>",
            request=request,
        )

    result = audit_url("retry.test", max_retries=1, client_factory=_mock_client_factory(handler))
    assert calls["count"] == 2
    assert result["status"] == "SUCCESS"
    assert result["title"] == "Recovered"
