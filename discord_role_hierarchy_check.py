# discord role hierarchy check
import discord


def can_moderate(actor: discord.Member, target: discord.Member) -> bool:
    owner_id = target.guild.owner_id
    # target-owner check must come first
    if target.id == owner_id:
        return False
    if actor.id == owner_id:
        return True
    # same as Role.__gt__, but mockable
    return actor.top_role.position > target.top_role.position


def bot_can_act_on(guild: discord.Guild, target: discord.Member) -> bool:
    # otherwise discord returns 403
    me = guild.me
    return target.id != guild.owner_id and me.top_role.position > target.top_role.position
