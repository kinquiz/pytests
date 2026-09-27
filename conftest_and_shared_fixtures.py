# conftest and shared fixtures
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_app_factory import create_app
from fastapi_router_and_depends import User, get_current_user
from putting_it_together_mini_project import DB_PATH_ENV, ModerationDB

AUDIT_CHANNEL_ID = 4242


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # env var so get_db_path() sees it
    path = tmp_path / "test.db"
    monkeypatch.setenv(DB_PATH_ENV, str(path))
    return path


@pytest.fixture
async def db(db_path: Path) -> AsyncIterator[ModerationDB]:
    async with ModerationDB() as database:
        yield database


@pytest.fixture
def fake_bot() -> MagicMock:
    bot = MagicMock(spec=commands.Bot)
    bot.get_channel.return_value = None  # empty channel cache
    bot.is_ready.return_value = True
    return bot


@pytest.fixture
def audit_channel(fake_bot: MagicMock) -> MagicMock:
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = AUDIT_CHANNEL_ID
    channel.send = AsyncMock()
    fake_bot.get_channel.side_effect = lambda cid: channel if cid == AUDIT_CHANNEL_ID else None
    return channel


@pytest.fixture
def current_user() -> User:
    return User("tester", is_admin=False)


@pytest.fixture
def app(current_user: User) -> Iterator[FastAPI]:
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: current_user
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
