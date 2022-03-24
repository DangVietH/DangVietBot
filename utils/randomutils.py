from io import BytesIO
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
from discord.ext import commands

cluster = AsyncIOMotorClient(config_var['mango_link'])
modrole = cluster["moderation"]['modrole']


def get_image_from_url(link):
    return BytesIO(requests.get(link).content)


def has_mod_role():
    async def predicate(ctx):
        result = await modrole.find_one({"guild": ctx.guild.id})
        if result is None:
            return False
        if ctx.guild.get_role(result['role']) in ctx.author.roles:
            return True

    return commands.check(predicate)