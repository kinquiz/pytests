# discord test helpers and mocks
import logging
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord import app_commands

from custom_exceptions import PermissionDenied
from discord_admin_check_and_custom_exception import (
    ADMIN_ROLE_NAME,
    AdminRoleRequired,
    admin_predicate,
    is_admin,
    is_admin_member,
)
from discord_cog_with_slash_command import FakeWarningsDB, Moderation
from discord_custom_command_tree import GatedCommandTree
from discord_embeds_helpers import MAX_DESCRIPTION, error_embed, info_embed, success_embed
from discord_error_handling import error_to_embed, respond_with_error
from discord_intents_and_bot_skeleton import PracticeBot, build_intents
from discord_role_hierarchy_check import bot_can_act_on, can_moderate

GUILD_ID = 1000
OWNER_ID = 1


def make_role(name: str = "Member", position: int = 1, role_id: int | None = None) -> MagicMock:
    role = MagicMock(spec=discord.Role)
    role.id = role_id if role_id is not None else 5000 + position
    role.name = name  # name= in the ctor names the mock
    role.position = position
    return role


def make_guild(*, guild_id: int = GUILD_ID, owner_id: int = OWNER_ID, bot_top_position: int = 50) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.owner_id = owner_id
    guild.name = "Test Guild"
    guild.me = make_member(9999, guild=guild, top_role_position=bot_top_position, bot=True)
    guild.get_channel.return_value = None
    guild.get_member.return_value = None
    return guild


def make_member(
    member_id: int,
    *,
    guild: MagicMock | None = None,
    top_role_position: int = 1,
    role_names: tuple[str, ...] = (),
    administrator: bool = False,
    bot: bool = False,
    display_name: str | None = None,
) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = member_id
    member.guild = guild if guild is not None else make_guild()
    member.bot = bot
    member.mention = f"<@{member_id}>"
    member.display_name = display_name or f"user{member_id}"
    member.name = member.display_name
    member.top_role = make_role("Top", top_role_position)
    member.roles = [make_role("@everyone", 0), *(make_role(n, i + 2) for i, n in enumerate(role_names)), member.top_role]
    member.guild_permissions = discord.Permissions(administrator=administrator)
    return member


def make_interaction(
    user: MagicMock,
    *,
    guild: MagicMock | None = None,
    command_name: str | None = None,
    response_done: bool = False,
) -> MagicMock:
    guild = guild if guild is not None else user.guild
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.guild = guild
    interaction.guild_id = guild.id if guild is not None else None

    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=response_done)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    if command_name is None:
        interaction.command = None
    else:
        command = MagicMock(spec=app_commands.Command)
        command.name = command_name.split()[-1]
        command.qualified_name = command_name
        interaction.command = command
    return interaction


def sent_embed(interaction: MagicMock) -> discord.Embed:
    for send in (interaction.response.send_message, interaction.followup.send):
        if send.await_count:
            return send.await_args.kwargs["embed"]
    raise AssertionError("nothing was sent")


def make_http_response(status: int, reason: str) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.reason = reason
    return resp


def test_mocks_pass_isinstance_checks():
    member = make_member(5)
    assert isinstance(member, discord.Member)
    assert isinstance(member.guild, discord.Guild)
    assert isinstance(make_interaction(member), discord.Interaction)


def test_spec_rejects_unknown_attributes():
    with pytest.raises(AttributeError):
        make_member(5).not_a_real_member_attribute  # noqa: B018


def test_intents():
    intents = build_intents()
    assert intents.members
    assert intents.guilds
    assert not intents.message_content


async def test_bot_constructs_with_custom_tree_and_no_connection():
    bot = PracticeBot(tree_cls=GatedCommandTree)
    assert isinstance(bot.tree, GatedCommandTree)
    assert not bot.is_ready()
    assert bot.user is None


async def test_setup_hook_logs_and_loads_extensions(caplog):
    bot = PracticeBot()
    bot.startup_extensions = ["discord_cog_with_slash_command"]
    with caplog.at_level(logging.INFO, logger="discord_intents_and_bot_skeleton"):
        await bot.setup_hook()
    try:
        assert "1 extension(s) loaded" in caplog.text
        assert bot.get_cog("Moderation") is not None
        assert {c.name for c in bot.tree.get_commands()} == {"warn", "warnings"}
    finally:
        await bot.unload_extension("discord_cog_with_slash_command")


def test_main_without_token_returns_error(monkeypatch):
    import discord_intents_and_bot_skeleton as skeleton

    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    monkeypatch.setattr(skeleton, "load_dotenv", lambda: None)
    assert skeleton.main() == 1


def test_embed_builders():
    ok = success_embed("saved")
    err = error_embed("nope", title="Bad")
    info = info_embed("Stats", fields={"Members": "10", "Bots": "2"})

    assert ok.title == "✅ Done" and ok.colour == discord.Colour.green()
    assert err.title == "❌ Bad" and err.description == "nope" and err.colour == discord.Colour.red()
    assert info.description is None
    assert [(f.name, f.value) for f in info.fields] == [("Members", "10"), ("Bots", "2")]


def test_embed_description_is_truncated():
    embed = success_embed("x" * 5000)
    assert len(embed.description) == MAX_DESCRIPTION
    assert embed.description.endswith("…")


class TestCanModerate:
    def setup_method(self):
        self.guild = make_guild()
        self.owner = make_member(OWNER_ID, guild=self.guild, top_role_position=1)
        self.admin = make_member(2, guild=self.guild, top_role_position=30)
        self.mod = make_member(3, guild=self.guild, top_role_position=20)
        self.member = make_member(4, guild=self.guild, top_role_position=1)

    def test_nobody_can_moderate_owner(self):
        assert not can_moderate(self.admin, self.owner)
        assert not can_moderate(self.owner, self.owner)

    def test_owner_can_moderate_anyone(self):
        # despite lower top role
        assert can_moderate(self.owner, self.admin)

    def test_higher_role_wins(self):
        assert can_moderate(self.admin, self.mod)
        assert can_moderate(self.mod, self.member)

    def test_lower_or_equal_role_loses(self):
        assert not can_moderate(self.mod, self.admin)
        peer = make_member(5, guild=self.guild, top_role_position=20)
        assert not can_moderate(self.mod, peer)

    def test_bot_can_act_on(self):
        assert bot_can_act_on(self.guild, self.admin)  # bot top role is 50
        assert not bot_can_act_on(self.guild, self.owner)
        high = make_member(6, guild=self.guild, top_role_position=60)
        assert not bot_can_act_on(self.guild, high)


def test_is_admin_member_variants():
    assert is_admin_member(make_member(2, administrator=True))
    assert is_admin_member(make_member(2, role_names=(ADMIN_ROLE_NAME,)))
    assert not is_admin_member(make_member(2, role_names=("Moderator",)))
    assert not is_admin_member(MagicMock(spec=discord.User))


async def test_admin_predicate_passes_for_admin():
    interaction = make_interaction(make_member(2, administrator=True), command_name="purge")
    assert await admin_predicate(interaction) is True


async def test_admin_predicate_raises_with_command_name():
    interaction = make_interaction(make_member(2), command_name="config set")
    with pytest.raises(AdminRoleRequired) as exc_info:
        await admin_predicate(interaction)
    assert exc_info.value.command_name == "config set"
    assert "/config set" in str(exc_info.value)
    assert isinstance(exc_info.value, app_commands.CheckFailure)


def test_is_admin_attaches_check():
    @app_commands.command(name="purge", description="x")
    @is_admin()
    async def purge(interaction: discord.Interaction) -> None: ...

    assert admin_predicate in purge.checks


@pytest.fixture
def cog() -> Moderation:
    return Moderation(MagicMock(), FakeWarningsDB())


async def test_warn_records_and_replies(cog):
    guild = make_guild()
    mod = make_member(2, guild=guild, top_role_position=20)
    target = make_member(3, guild=guild, top_role_position=1)
    interaction = make_interaction(mod, command_name="warn")

    await cog.warn.callback(cog, interaction, target, "spam")

    entries = await cog.db.get_warnings(GUILD_ID, 3)
    assert [(e.moderator_id, e.reason) for e in entries] == [(2, "spam")]
    embed = sent_embed(interaction)
    assert embed.title == "✅ Warned"
    assert "(1 total)" in embed.description


async def test_warn_refuses_higher_target(cog):
    guild = make_guild()
    mod = make_member(2, guild=guild, top_role_position=5)
    target = make_member(3, guild=guild, top_role_position=10)
    interaction = make_interaction(mod, command_name="warn")

    await cog.warn.callback(cog, interaction, target, "spam")

    assert await cog.db.get_warnings(GUILD_ID, 3) == []
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True
    assert "can't moderate" in sent_embed(interaction).description


async def test_warn_refuses_bots(cog):
    guild = make_guild()
    interaction = make_interaction(make_member(OWNER_ID, guild=guild), command_name="warn")
    await cog.warn.callback(cog, interaction, make_member(7, guild=guild, bot=True), "x")
    assert sent_embed(interaction).description == "Bots can't be warned."


async def test_warnings_lists_entries(cog):
    await cog.db.add_warning(GUILD_ID, 3, 2, "first")
    await cog.db.add_warning(GUILD_ID, 3, 2, "second")
    interaction = make_interaction(make_member(2))

    await cog.warnings.callback(cog, interaction, make_member(3, display_name="bob"))

    embed = sent_embed(interaction)
    assert embed.title == "Warnings for bob"
    assert [f.value.split(" (")[0] for f in embed.fields] == ["first", "second"]


async def test_warnings_empty(cog):
    interaction = make_interaction(make_member(2))
    await cog.warnings.callback(cog, interaction, make_member(3))
    assert "No warnings" in sent_embed(interaction).description


@pytest.fixture
def tree() -> GatedCommandTree:
    # real Client, but no network until sync()/start()
    return PracticeBot(tree_cls=GatedCommandTree).tree


async def test_tree_gates_admin_commands(tree):
    interaction = make_interaction(make_member(2), command_name="purge")
    with pytest.raises(AdminRoleRequired):
        await tree.interaction_check(interaction)


async def test_tree_lets_admin_through(tree):
    interaction = make_interaction(make_member(2, role_names=(ADMIN_ROLE_NAME,)), command_name="config set")
    assert await tree.interaction_check(interaction) is True


@pytest.mark.parametrize("command_name", ["warn", "warnings", None])
async def test_tree_ignores_other_commands(tree, command_name):
    interaction = make_interaction(make_member(2), command_name=command_name)
    assert await tree.interaction_check(interaction) is True


async def test_tree_on_error_sends_embed(tree):
    interaction = make_interaction(make_member(2), command_name="purge")
    await tree.on_error(interaction, AdminRoleRequired("purge"))
    assert sent_embed(interaction).title == "❌ Admins only"


@pytest.mark.parametrize(
    ("error", "expected_title", "expected_text"),
    [
        (AdminRoleRequired("purge"), "Admins only", "/purge"),
        (app_commands.MissingPermissions(["ban_members"]), "Missing permissions", "Ban Members"),
        (app_commands.BotMissingPermissions(["manage_roles"]), "Bot missing permissions", "Manage Roles"),
        (app_commands.CommandOnCooldown(app_commands.Cooldown(1, 30), 12.4), "Slow down", "12s"),
        (app_commands.NoPrivateMessage(), "Error", "only works in a server"),
        (app_commands.CheckFailure(), "Not allowed", "can't use"),
        (PermissionDenied("ban", required="admin"), "Not allowed", "'ban'"),
        (discord.Forbidden(make_http_response(403, "Forbidden"), "Missing Access"), "Forbidden", "role position"),
        (discord.NotFound(make_http_response(404, "Not Found"), "Unknown Message"), "Not found", "no longer"),
        (discord.HTTPException(make_http_response(500, "Server Error"), "boom"), "Error", "Discord returned"),
        (RuntimeError("bug"), "Error", "Something went wrong"),
    ],
)
def test_error_to_embed(error, expected_title, expected_text):
    embed = error_to_embed(error)
    assert embed.title == f"❌ {expected_title}"
    assert expected_text in embed.description


def test_invoke_error_is_unwrapped():
    command = MagicMock(spec=app_commands.Command)
    command.name = "ban"  # instance attr, not covered by spec
    wrapped = app_commands.CommandInvokeError(command, discord.Forbidden(make_http_response(403, "Forbidden"), "x"))
    assert error_to_embed(wrapped).title == "❌ Forbidden"


async def test_respond_uses_followup_when_already_responded():
    interaction = make_interaction(make_member(2), response_done=True)
    await respond_with_error(interaction, app_commands.CheckFailure())
    interaction.response.send_message.assert_not_awaited()
    interaction.followup.send.assert_awaited_once()


async def test_unexpected_errors_are_logged(caplog):
    interaction = make_interaction(make_member(2))
    with caplog.at_level(logging.ERROR, logger="discord_error_handling"):
        await respond_with_error(interaction, RuntimeError("bug"))
    assert "unhandled error" in caplog.text
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True
