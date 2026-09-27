# discord error handling
import logging

import discord
from discord import app_commands

from custom_exceptions import PermissionDenied
from discord_admin_check_and_custom_exception import AdminRoleRequired
from discord_embeds_helpers import error_embed

log = logging.getLogger(__name__)


def _fmt_perms(perms: list[str]) -> str:
    return ", ".join(p.replace("_", " ").title() for p in perms)


def error_to_embed(error: Exception) -> discord.Embed:
    # errors from the command body arrive wrapped
    if isinstance(error, app_commands.CommandInvokeError):
        error = error.original

    # subclasses before CheckFailure
    if isinstance(error, AdminRoleRequired):
        return error_embed(str(error), title="Admins only")
    elif isinstance(error, app_commands.MissingPermissions):
        return error_embed(f"You're missing: {_fmt_perms(error.missing_permissions)}", title="Missing permissions")
    elif isinstance(error, app_commands.BotMissingPermissions):
        return error_embed(f"I'm missing: {_fmt_perms(error.missing_permissions)}", title="Bot missing permissions")
    elif isinstance(error, app_commands.CommandOnCooldown):
        return error_embed(f"Try again in {error.retry_after:.0f}s.", title="Slow down")
    elif isinstance(error, app_commands.NoPrivateMessage):
        return error_embed("This command only works in a server.")
    elif isinstance(error, app_commands.CheckFailure):
        return error_embed("You can't use this command here.", title="Not allowed")
    elif isinstance(error, PermissionDenied):
        return error_embed(str(error), title="Not allowed")
    elif isinstance(error, discord.Forbidden):
        return error_embed("I don't have permission to do that (check my role position).", title="Forbidden")
    elif isinstance(error, discord.NotFound):
        return error_embed("That no longer exists.", title="Not found")
    elif isinstance(error, discord.HTTPException):
        return error_embed("Discord returned an error, try again shortly.")
    else:
        return error_embed("Something went wrong. It's been logged.")


async def respond_with_error(interaction: discord.Interaction, error: Exception) -> None:
    embed = error_to_embed(error)
    if not isinstance(error, (app_commands.CheckFailure, app_commands.CommandOnCooldown)):
        log.error("unhandled error in command", exc_info=error)
    # response is single-use
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)
