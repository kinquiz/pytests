# session auth with fastapi
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from bcrypt_password_hashing import authenticate, hash_password
from login_rate_limiting import LoginRateLimiter

SESSION_COOKIE = "dashboard_session"


def require_login(request: Request) -> str:
    username = request.session.get("user")
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login required")
    return username


LoggedInUser = Annotated[str, Depends(require_login)]


def create_session_app(
    *,
    secret_key: str,
    users: dict[str, str],
    limiter: LoginRateLimiter | None = None,
    https_only: bool = True,
    bcrypt_rounds: int = 12,
) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie=SESSION_COOKIE,
        max_age=60 * 60 * 8,
        same_site="lax",
        https_only=https_only,
    )
    # empty limiter is falsy (__len__)
    if limiter is None:
        limiter = LoginRateLimiter()

    @app.post("/login")
    async def login(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ) -> RedirectResponse:
        ip = request.client.host if request.client else "unknown"
        if limiter.is_blocked(ip):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "too many failed logins",
                headers={"Retry-After": str(int(limiter.retry_after(ip)) + 1)},
            )
        if not authenticate(username, password, users, rounds=bcrypt_rounds):
            limiter.record_failure(ip)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")

        limiter.reset(ip)
        request.session.clear()  # avoid session fixation
        request.session["user"] = username
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/logout")
    async def logout(request: Request) -> RedirectResponse:
        request.session.clear()
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/dashboard")
    async def dashboard(user: LoggedInUser) -> dict[str, str]:
        return {"message": f"welcome, {user}"}

    return app


TEST_USERS = {"admin": hash_password("s3cret", rounds=4)}


def _app(**kwargs) -> FastAPI:
    # TestClient uses plain http
    return create_session_app(secret_key="test-key", users=TEST_USERS, https_only=False, bcrypt_rounds=4, **kwargs)


def _login(client: TestClient, password: str = "s3cret"):
    return client.post("/login", data={"username": "admin", "password": password}, follow_redirects=False)


def test_dashboard_requires_login():
    assert TestClient(_app()).get("/dashboard").status_code == 401


def test_login_sets_cookie_and_redirects():
    client = TestClient(_app())
    resp = _login(client)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/dashboard"
    assert SESSION_COOKIE in resp.cookies
    assert client.get("/dashboard").json() == {"message": "welcome, admin"}


def test_wrong_password():
    client = TestClient(_app())
    assert _login(client, "nope").status_code == 401
    assert client.get("/dashboard").status_code == 401


def test_logout_clears_session():
    client = TestClient(_app())
    _login(client)
    client.post("/logout", follow_redirects=False)
    assert client.get("/dashboard").status_code == 401


def test_tampered_cookie_is_ignored():
    client = TestClient(_app())
    client.cookies.set(SESSION_COOKIE, "eyJ1c2VyIjogImFkbWluIn0=.forged.signature")
    assert client.get("/dashboard").status_code == 401


def test_rate_limit_kicks_in():
    client = TestClient(_app(limiter=LoginRateLimiter(max_attempts=2)))
    assert _login(client, "x").status_code == 401
    assert _login(client, "x").status_code == 401
    blocked = _login(client)  # correct password, still blocked
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_dependency_override_skips_login():
    app = _app()
    app.dependency_overrides[require_login] = lambda: "overridden"
    assert TestClient(app).get("/dashboard").json() == {"message": "welcome, overridden"}
