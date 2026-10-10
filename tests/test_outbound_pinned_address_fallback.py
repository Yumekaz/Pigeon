import ipaddress

import httpcore
import httpx
import pytest

from src.outbound_fetch import _PinnedBackend, _get_public_url


def test_search_content_shim_uses_production_address_fallback(monkeypatch):
    from services.search import content
    captured = {}
    def fetch(url, **kwargs):
        captured.update(kwargs)
        return 'response'
    monkeypatch.setattr(content._outbound_fetch, '_get_public_url', fetch)
    assert content._get_public_url('https://public.example', {}, 10) == 'response'
    assert captured['transport_factory'] is None
    assert captured['resolve_public_ips'] is content._resolve_public_ips


def test_tls_timeout_falls_back_to_next_pinned_address(monkeypatch):
    from src import outbound_fetch
    calls = []

    class Transport:
        def __init__(self, address): self.address = address
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def handle_request(self, request):
            calls.append((str(self.address), request.url.host, request.extensions['timeout']['connect']))
            if self.address.version == 6:
                raise httpx.ConnectTimeout('TLS unavailable')
            return httpx.Response(200, content=b'public reference')

    monkeypatch.setattr(outbound_fetch, '_PinnedTransport', Transport)
    transport = outbound_fetch._AddressFallbackTransport([
        ipaddress.ip_address('2606:4700::1111'), ipaddress.ip_address('1.1.1.1')], 10)
    result = transport.handle_request(httpx.Request('GET', 'https://public.example/reference'))
    assert result.content == b'public reference'
    assert [c[:2] for c in calls] == [('2606:4700::1111', 'public.example'), ('1.1.1.1', 'public.example')]
    assert 0 < calls[0][2] <= 5


def test_connect_falls_back_without_resolving_host_again(monkeypatch):
    calls = []
    stream = object()

    class Network:
        def connect_tcp(self, host, port, timeout, local_address, socket_options):
            calls.append((host, port, timeout))
            if ':' in host:
                raise httpcore.ConnectTimeout('IPv6 unavailable')
            return stream

    monkeypatch.setattr(httpcore, 'SyncBackend', Network)
    backend = _PinnedBackend(ipaddress.ip_address('2606:4700::1111'),
                             fallback_ips=[ipaddress.ip_address('1.1.1.1')])
    assert backend.connect_tcp('public.example', 443, timeout=10) is stream
    assert [c[0] for c in calls] == ['2606:4700::1111', '1.1.1.1']
    assert 0 < calls[0][2] <= 5
    assert 0 < calls[1][2] <= 10


def test_all_connection_failures_preserve_failure(monkeypatch):
    class Network:
        def connect_tcp(self, *args):
            raise httpcore.ConnectError('unavailable')
    monkeypatch.setattr(httpcore, 'SyncBackend', Network)
    backend = _PinnedBackend(ipaddress.ip_address('1.1.1.1'),
                             fallback_ips=[ipaddress.ip_address('8.8.8.8')])
    with pytest.raises(httpcore.ConnectError):
        backend.connect_tcp('public.example', 443, timeout=1)


def test_mixed_public_private_dns_is_rejected_before_transport(monkeypatch):
    from src import outbound_fetch
    monkeypatch.setattr(outbound_fetch, '_resolve_hostname_ips', lambda host: [
        ipaddress.ip_address('1.1.1.1'), ipaddress.ip_address('127.0.0.1'),
    ])
    def forbidden_transport(*args):
        raise AssertionError('transport must not connect')
    with pytest.raises(Exception, match='Blocked non-public URL'):
        _get_public_url('https://public.example', {}, 1, transport_factory=forbidden_transport)
