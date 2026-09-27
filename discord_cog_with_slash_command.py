# discord cog with slash command
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from discord_embeds_helpers import error_embed, info_embed, success_embed
from discord_role_hierarchy_check import can_moderate


@dataclass
class WarningEntry:
    moderator_id: int
    reason: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FakeWarningsDB:
    # same async interface as the real DB layer
    def __init__(self) -> None:
        self._data: dict[tuple[int, int], list[WarningEntry]] = defaultdict(list)

    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        self._data[(guild_id, user_id)].append(WarningEntry(moderator_id, reason))
        return len(self._data[(guild_id, user_id)])

    async def get_warnings(self, guild_id: int, user_id: int) -> list[WarningEntry]:
        return list(self._data.get((guild_id, user_id), []))


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot, db: FakeWarningsDB) -> None:
        self.bot = bot
        self.db = db

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Who to warn", reason="Why")
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason given") -> None:
        if member.bot:
            await interaction.response.send_message(embed=error_embed("Bots can't be warned."), ephemeral=True)
            return
        if not can_moderate(interaction.user, member):
            await interaction.response.send_message(
                embed=error_embed(f"You can't moderate {member.mention}."), ephemeral=True
            )
            return

        count = await self.db.add_warning(interaction.guild_id, member.id, interaction.user.id, reason)
        await interaction.response.send_message(
            embed=success_embed(f"{member.mention} has been warned ({count} total).\nReason: {reason}", title="Warned")
        )

    @app_commands.command(name="warnings", description="List a member's warnings")
    @app_commands.guild_only()
    async def warnings(self, interaction: discord.Interaction, member: discord.Member) -> None:
        entries = await self.db.get_warnings(interaction.guild_id, member.id)
        if not entries:
            embed = info_embed(f"Warnings for {member.display_name}", "No warnings. 🎉")
        else:
            fields = {
                f"#{i} · {e.created_at:%Y-%m-%d}": f"{e.reason} (by <@{e.moderator_id}>)"
                for i, e in enumerate(entries, start=1)
            }
            embed = info_embed(f"Warnings for {member.display_name}", f"{len(entries)} total", fields=fields)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot, FakeWarningsDB()))
