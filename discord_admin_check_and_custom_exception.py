# discord admin check and custom exception
import discord
from discord import app_commands

ADMIN_ROLE_NAME = "Admin"


class AdminRoleRequired(app_commands.CheckFailure):
    # CheckFailure so the tree's on_error handles it
    def __init__(self, command_name: str | None = None) -> None:
        self.command_name = command_name
        target = f"/{command_name}" if command_name else "this command"
        super().__init__(f"You need the {ADMIN_ROLE_NAME} role to use {target}.")


def is_admin_member(member: discord.Member | discord.User) -> bool:
    if not isinstance(member, discord.Member):
        return False  # DMs: no roles
    if member.guild_permissions.administrator:
        return True
    return any(role.name == ADMIN_ROLE_NAME for role in member.roles)


async def admin_predicate(interaction: discord.Interaction) -> bool:
    if is_admin_member(interaction.user):
        return True
    command = interaction.command
    raise AdminRoleRequired(command.qualified_name if command else None)


def is_admin():
    return app_commands.check(admin_predicate)
