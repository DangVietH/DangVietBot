import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
import aiohttp

cluster = AsyncIOMotorClient(config_var['mango_link'])

cursor = cluster['bot']['gc']


class GlobalChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            server = await cursor.find_one({"guild": message.guild.id})
            if server is not None:
                if message.channel == self.bot.get_channel(server['channel']):
                    if not message.content:
                        return
                    else:
                        alGuild = cursor.find()
                        async for guild in alGuild:
                            if guild['guild'] != message.guild.id:
                                async with aiohttp.ClientSession() as session:
                                    webhook = discord.Webhook.from_url(guild['webhook'], session=session)
                                    await webhook.send(
                                        content=message.content,
                                        username=message.author,
                                        avatar_url=message.author.display_avatar.url
                                    )
            else:
                return None

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursor.find_one({"guild": guild.id})
        if result is not None:
            await cursor.delete_one({"guild": guild.id})