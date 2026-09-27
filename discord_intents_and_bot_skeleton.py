# discord intents and bot skeleton
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

log = logging.getLogger(__name__)


def build_intents() -> discord.Intents:
    # members is privileged: also enable in dev portal
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = False  # not needed for slash commands
    return intents


class PracticeBot(commands.Bot):
    def __init__(self, *, tree_cls: type[app_commands.CommandTree] = app_commands.CommandTree) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=build_intents(),
            tree_cls=tree_cls,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
        )
        self.startup_extensions: list[str] = []

    async def setup_hook(self) -> None:
        # once, after login, before gateway connect
        for ext in self.startup_extensions:
            await self.load_extension(ext)
        log.info("setup_hook done, %d extension(s) loaded", len(self.startup_extensions))

    async def on_ready(self) -> None:
        log.info("logged in as %s (id=%s)", self.user, self.user.id if self.user else "?")


def main() -> int:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        log.error("DISCORD_TOKEN is not set (see .env.example)")
        return 1
    logging.basicConfig(level=logging.INFO)
    PracticeBot().run(token, log_handler=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
