# custom middleware ip allowlist
import ipaddress
import logging
from collections.abc import Iterable
from ipaddress import IPv4Network, IPv6Network

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from fastapi_app_factory import create_app
from fastapi_router_and_depends import User, get_current_user

log = logging.getLogger(__name__)

Network = IPv4Network | IPv6Network


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, allowed: Iterable[str | Network]) -> None:
        super().__init__(app)
        self.networks: list[Network] = [ipaddress.ip_network(n, strict=False) for n in allowed]
        if not self.networks:
            log.warning("IP allowlist is empty - every request will be rejected")

    def is_allowed(self, host: str | None) -> bool:
        if not self.networks or not host:
            return False
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            return False
        # ::ffff:a.b.c.d -> IPv4
        if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
            addr = addr.ipv4_mapped
        return any(addr in net for net in self.networks)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # direct peer; use uvicorn --proxy-headers behind a proxy
        host = request.client.host if request.client else None
        if not self.is_allowed(host):
            log.info("blocked request from %s to %s", host, request.url.path)
            return PlainTextResponse("Forbidden", status_code=403)
        return await call_next(request)


def create_protected_app(allowed: Iterable[str]) -> FastAPI:
    app = create_app()
    app.add_middleware(IPAllowlistMiddleware, allowed=list(allowed))
    return app


def _client(allowed: list[str], ip: str) -> TestClient:
    app = create_protected_app(allowed)
    app.dependency_overrides[get_current_user] = lambda: User("tester")
    # fake peer address
    return TestClient(app, client=(ip, 50000))


def test_allowed_ip_passes():
    resp = _client(["127.0.0.1"], "127.0.0.1").get("/api/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "tester"


def test_ip_in_cidr_range_passes():
    assert _client(["10.0.0.0/8"], "10.20.30.40").get("/api/health").status_code == 200


def test_ip_outside_range_is_blocked():
    resp = _client(["10.0.0.0/8", "192.168.1.0/24"], "192.168.2.1").get("/api/health")
    assert resp.status_code == 403
    assert resp.text == "Forbidden"


def test_empty_allowlist_fails_closed():
    assert _client([], "127.0.0.1").get("/api/health").status_code == 403


def test_non_ip_client_host_is_blocked():
    # default host 'testclient' isn't an IP
    app = create_protected_app(["0.0.0.0/0"])
    assert TestClient(app).get("/api/health").status_code == 403


def test_ipv6_and_mapped_ipv4():
    assert _client(["::1"], "::1").get("/api/health").status_code == 200
    assert _client(["127.0.0.1"], "::ffff:127.0.0.1").get("/api/health").status_code == 200
    assert _client(["127.0.0.1"], "::1").get("/api/health").status_code == 403


def test_blocked_request_never_reaches_dependency():
    calls = []
    app = create_protected_app(["10.0.0.1"])
    app.dependency_overrides[get_current_user] = lambda: calls.append(1) or User("x")
    TestClient(app, client=("8.8.8.8", 1)).get("/api/me")
    assert calls == []
