# discord embeds helpers
import discord

SUCCESS_COLOUR = discord.Colour.green()
ERROR_COLOUR = discord.Colour.red()
INFO_COLOUR = discord.Colour.blurple()

# discord embed description limit
MAX_DESCRIPTION = 4096


def _truncate(text: str, limit: int = MAX_DESCRIPTION) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _embed(title: str, description: str | None, colour: discord.Colour) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=_truncate(description) if description else None,
        colour=colour,
    )


def success_embed(description: str, *, title: str = "Done") -> discord.Embed:
    return _embed(f"✅ {title}", description, SUCCESS_COLOUR)


def error_embed(description: str, *, title: str = "Error") -> discord.Embed:
    return _embed(f"❌ {title}", description, ERROR_COLOUR)


def info_embed(title: str, description: str | None = None, *, fields: dict[str, str] | None = None) -> discord.Embed:
    embed = _embed(title, description, INFO_COLOUR)
    for name, value in (fields or {}).items():
        embed.add_field(name=name, value=value, inline=False)
    return embed
