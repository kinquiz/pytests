# discord custom command tree
import discord
from discord import app_commands

from discord_admin_check_and_custom_exception import admin_predicate
from discord_error_handling import respond_with_error

ADMIN_ONLY_COMMANDS: frozenset[str] = frozenset({"purge", "config", "config set", "lockdown"})


class GatedCommandTree(app_commands.CommandTree):
    admin_only: frozenset[str] = ADMIN_ONLY_COMMANDS

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        command = interaction.command
        if command is None:
            return True  # autocomplete/components
        if command.qualified_name in self.admin_only:
            # raises AdminRoleRequired -> on_error
            return await admin_predicate(interaction)
        return True

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError, /) -> None:
        await respond_with_error(interaction, error)
