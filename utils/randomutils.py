from io import BytesIO
import requests
from discord.ext import commands


def get_image_from_url(link):
    return BytesIO(requests.get(link).content)


def has_mod_role():
    async def predicate(ctx):
        modrole = ctx.bot.mongo["moderation"]['modrole']
        result = await modrole.find_one({"guild": ctx.guild.id})
        if result is None:
            return False
        if ctx.guild.get_role(result['role']) in ctx.author.roles:
            return True

    return commands.check(predicate)