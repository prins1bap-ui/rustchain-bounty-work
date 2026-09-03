from __future__ import annotations

import ipaddress
import socket

import httpcore
import httpx

from .scanner import DnsResolutionError, UnsafeUrlError


class PublicOnlyNetworkBackend(httpcore.SyncBackend):
    """Resolve, validate, then connect to the validated public IP directly.

    URL validation alone is not sufficient for SSRF protection because DNS can
    change between validation and the socket connection. This backend performs
    a fresh resolution at connection time, rejects the whole host if any answer
    is non-global, and passes a literal validated IP to httpcore's socket layer.
    TLS still uses the original hostname because httpcore retains the request
    origin and applies it when starting TLS on the returned stream.
    """

    @staticmethod
    def _resolve_public_addresses(host: str) -> list[ipaddress._BaseAddress]:
        host_text = host.decode("ascii") if isinstance(host, bytes) else str(host)
        literal_candidate = host_text.strip("[]")
        try:
            addresses = [ipaddress.ip_address(literal_candidate)]
        except ValueError:
            try:
                infos = socket.getaddrinfo(host_text, None, proto=socket.IPPROTO_TCP)
            except socket.gaierror as exc:
                raise DnsResolutionError("Hostname could not be resolved at connection time") from exc

            seen: set[str] = set()
            addresses = []
            for info in infos:
                ip_text = info[4][0]
                if ip_text in seen:
                    continue
                seen.add(ip_text)
                addresses.append(ipaddress.ip_address(ip_text))

        if not addresses:
            raise DnsResolutionError("Hostname could not be resolved at connection time")
        if any(not address.is_global for address in addresses):
            raise UnsafeUrlError(
                "DNS resolved to a private, local, reserved, or otherwise non-global address"
            )
        return addresses

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None,
    ):
        addresses = self._resolve_public_addresses(host)
        last_error: Exception | None = None
        for address in addresses:
            try:
                # Passing a literal IP prevents another hostname resolution from
                # redirecting the socket to a different address after validation.
                return super().connect_tcp(
                    str(address),
                    port,
                    timeout=timeout,
                    local_address=local_address,
                    socket_options=socket_options,
                )
            except Exception as exc:  # httpcore ConnectError/ConnectTimeout; try next public IP.
                last_error = exc
        assert last_error is not None
        raise last_error


class PublicOnlyHTTPTransport(httpx.HTTPTransport):
    """HTTPX transport with environment proxies disabled and public-IP pinning."""

    def __init__(self) -> None:
        # This implementation intentionally targets the pinned httpx/httpcore
        # versions in requirements.txt. HTTPTransport does not expose a public
        # network-backend constructor argument, so replace the pool backend after
        # normal initialization and verify this behavior in deterministic tests.
        super().__init__(trust_env=False, retries=0)
        self._pool._network_backend = PublicOnlyNetworkBackend()  # noqa: SLF001


def public_client_factory(*args, **kwargs) -> httpx.Client:
    """Create the scanner client without proxy inheritance and with IP pinning."""
    kwargs["trust_env"] = False
    kwargs["transport"] = PublicOnlyHTTPTransport()
    return httpx.Client(*args, **kwargs)
