# jinja2 templates and static
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

INDEX_TEMPLATE = """\
<!doctype html>
<html>
<head>
  <title>{{ title }}</title>
  <link rel="stylesheet" href="{{ url_for('static', path='style.css') }}">
</head>
<body>
  <h1>{{ title }}</h1>
  {% if guilds %}
  <ul>
    {% for guild in guilds %}<li>{{ guild.name }} ({{ guild.members }} members)</li>
    {% endfor %}
  </ul>
  {% else %}
  <p>No guilds yet.</p>
  {% endif %}
  <footer>{{ note }}</footer>
</body>
</html>
"""

STYLE_CSS = "body { font-family: sans-serif; max-width: 40rem; margin: 2rem auto; }\n"


def prepare_assets(base_dir: Path) -> tuple[Path, Path]:
    templates_dir = base_dir / "templates"
    static_dir = base_dir / "static"
    templates_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "index.html").write_text(INDEX_TEMPLATE, encoding="utf-8")
    (static_dir / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    return templates_dir, static_dir


def create_templated_app(base_dir: Path, guilds: list[dict] | None = None) -> FastAPI:
    templates_dir, static_dir = prepare_assets(base_dir)
    templates = Jinja2Templates(directory=templates_dir)  # autoescapes .html
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"title": "Dashboard", "guilds": guilds or [], "note": "<b>not bold</b>"},
        )

    return app


def test_index_renders_variables(tmp_path):
    guilds = [{"name": "Python Help", "members": 120}, {"name": "Test Server", "members": 3}]
    resp = TestClient(create_templated_app(tmp_path, guilds)).get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "<title>Dashboard</title>" in resp.text
    assert "<li>Python Help (120 members)</li>" in resp.text


def test_empty_state(tmp_path):
    assert "No guilds yet." in TestClient(create_templated_app(tmp_path)).get("/").text


def test_autoescape(tmp_path):
    body = TestClient(create_templated_app(tmp_path)).get("/").text
    assert "&lt;b&gt;not bold&lt;/b&gt;" in body


def test_static_file_served_and_linked(tmp_path):
    client = TestClient(create_templated_app(tmp_path))
    assert 'href="http://testserver/static/style.css"' in client.get("/").text
    css = client.get("/static/style.css")
    assert css.status_code == 200
    assert "font-family" in css.text
    assert client.get("/static/missing.css").status_code == 404
