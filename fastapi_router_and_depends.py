# fastapi router and depends
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from fastapi.testclient import TestClient


@dataclass(frozen=True)
class User:
    username: str
    is_admin: bool = False


FAKE_USERS = {
    "ann": User("ann", is_admin=True),
    "bob": User("bob"),
}


def get_current_user(x_user: Annotated[str | None, Header()] = None) -> User:
    # X-User header
    user = FAKE_USERS.get(x_user or "")
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not logged in")
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admins only")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/me")
async def me(user: CurrentUser) -> dict[str, object]:
    return {"username": user.username, "is_admin": user.is_admin}


@router.get("/admin/stats")
async def admin_stats(user: AdminUser) -> dict[str, object]:
    return {"requested_by": user.username, "guilds": 3, "warnings": 42}


def _client(overrides: dict | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides.update(overrides or {})
    return TestClient(app)


def test_health_needs_no_user():
    assert _client().get("/api/health").json() == {"status": "ok"}


def test_me_without_user_is_401():
    assert _client().get("/api/me").status_code == 401


def test_me_via_header():
    resp = _client().get("/api/me", headers={"X-User": "bob"})
    assert resp.json() == {"username": "bob", "is_admin": False}


def test_me_with_dependency_override():
    client = _client({get_current_user: lambda: User("override", is_admin=False)})
    assert client.get("/api/me").json()["username"] == "override"


def test_admin_stats_forbidden_for_non_admin():
    client = _client({get_current_user: lambda: User("bob")})
    resp = client.get("/api/admin/stats")
    assert resp.status_code == 403
    assert resp.json() == {"detail": "admins only"}


def test_admin_stats_for_admin():
    # require_admin still runs on top
    client = _client({get_current_user: lambda: User("root", is_admin=True)})
    assert client.get("/api/admin/stats").json()["requested_by"] == "root"


def test_override_require_admin_directly():
    client = _client({require_admin: lambda: User("skip-checks", is_admin=True)})
    assert client.get("/api/admin/stats").status_code == 200
