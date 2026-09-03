import socket

import httpcore
import pytest

from src.public_transport import PublicOnlyHTTPTransport, PublicOnlyNetworkBackend, public_client_factory
from src.scanner import DnsResolutionError, UnsafeUrlError


def _public_ipv4_info(host, port, proto=None):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 0))]


def test_connection_time_dns_is_pinned_to_validated_literal_ip(monkeypatch):
    monkeypatch.setattr("src.public_transport.socket.getaddrinfo", _public_ipv4_info)
    connected_hosts = []
    sentinel = object()

    def fake_base_connect(self, host, port, timeout=None, local_address=None, socket_options=None):
        connected_hosts.append(host)
        return sentinel

    monkeypatch.setattr(httpcore.SyncBackend, "connect_tcp", fake_base_connect)
    backend = PublicOnlyNetworkBackend()

    assert backend.connect_tcp("example.test", 443) is sentinel
    assert connected_hosts == ["93.184.216.34"]


def test_connection_time_dns_rejects_private_answer_before_socket(monkeypatch):
    def private_info(host, port, proto=None):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 0))]

    monkeypatch.setattr("src.public_transport.socket.getaddrinfo", private_info)
    monkeypatch.setattr(
        httpcore.SyncBackend,
        "connect_tcp",
        lambda *args, **kwargs: pytest.fail("Socket connection must not be attempted"),
    )

    with pytest.raises(UnsafeUrlError):
        PublicOnlyNetworkBackend().connect_tcp("rebind.test", 80)


def test_connection_time_dns_rejects_mixed_public_private_answers(monkeypatch):
    def mixed_info(host, port, proto=None):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.8", 0)),
        ]

    monkeypatch.setattr("src.public_transport.socket.getaddrinfo", mixed_info)
    with pytest.raises(UnsafeUrlError):
        PublicOnlyNetworkBackend().connect_tcp("mixed.test", 443)


def test_connection_time_dns_failure_is_structured(monkeypatch):
    def failed_info(host, port, proto=None):
        raise socket.gaierror("gone")

    monkeypatch.setattr("src.public_transport.socket.getaddrinfo", failed_info)
    with pytest.raises(DnsResolutionError):
        PublicOnlyNetworkBackend().connect_tcp("gone.test", 443)


def test_literal_private_target_is_rejected_without_dns(monkeypatch):
    monkeypatch.setattr(
        "src.public_transport.socket.getaddrinfo",
        lambda *args, **kwargs: pytest.fail("Literal IP must not require DNS"),
    )
    with pytest.raises(UnsafeUrlError):
        PublicOnlyNetworkBackend().connect_tcp("127.0.0.1", 80)


def test_public_client_factory_installs_hardened_backend_and_disables_proxy_inheritance():
    client = public_client_factory()
    try:
        assert isinstance(client._transport, PublicOnlyHTTPTransport)
        assert isinstance(client._transport._pool._network_backend, PublicOnlyNetworkBackend)
    finally:
        client.close()
