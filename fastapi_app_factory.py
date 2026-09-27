# fastapi app factory
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_router_and_depends import User, get_current_user, router


def create_app(*, title: str = "Practice Dashboard", debug: bool = False) -> FastAPI:
    app = FastAPI(title=title, debug=debug, docs_url="/docs" if debug else None, redoc_url=None)
    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"app": title}

    return app


def test_factory_returns_independent_apps():
    a, b = create_app(), create_app()
    a.dependency_overrides[get_current_user] = lambda: User("a")
    assert a is not b
    assert b.dependency_overrides == {}


def test_router_is_mounted():
    client = TestClient(create_app(title="Test"))
    assert client.get("/").json() == {"app": "Test"}
    assert client.get("/api/health").status_code == 200


def test_docs_only_in_debug():
    assert TestClient(create_app()).get("/docs").status_code == 404
    assert TestClient(create_app(debug=True)).get("/docs").status_code == 200


def test_mounted_router_uses_overrides():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User("tester", is_admin=True)
    with TestClient(app) as client:  # runs lifespan events
        assert client.get("/api/me").json() == {"username": "tester", "is_admin": True}
