import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
cursor = cluster["moderation"]['automod']


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

    @commands.Cog.listener(name="on_message")
    async def when_automod(self, message: discord.Message):
        if message.guild:
            check = await cursor.find_one({"guild": message.guild.id})
            if check is None:
                return
            else:
                if message.author.bot:
                    return
                elif not isinstance(message.author, discord.Member):
                    return
                elif message.author.guild_permissions.administrator:
                    return
                else:
                    await self.is_blacklist(message)

    @commands.Cog.listener(name="on_message_edit")
    async def when_automod_is_edit(self, before, after):
        message = after
        if message.guild:
            check = await cursor.find_one({"guild": message.guild.id})
            if check is None:
                return
            else:
                if message.author.bot:
                    return
                elif not isinstance(message.author, discord.Member):
                    return
                elif message.author.guild_permissions.administrator:
                    return
                else:
                    await self.is_blacklist(message)

    async def is_blacklist(self, message):
        check = await cursor.find_one({"guild": message.guild.id, "blacklist": message.content.lower()})
        if check is not None:
            await message.delete()
            await message.author.send("That's a blacklisted word")
