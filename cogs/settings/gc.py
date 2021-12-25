import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
import datetime

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))

db = cluster['bot']
cursor = db['gc']


class GlobalChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            server = await cursor.find_one({"guild": message.guild.id})
            if message.channel == self.bot.get_channel(server['channel']):
                if not message.content:
                    return
                else:
                    alChannels = cursor.find()
                    async for channel in alChannels:
                        if channel['channel'] != message.channel.id:
                            embed = discord.Embed(description=message.content, timestamp=datetime.datetime.utcnow(), color=discord.Color.from_rgb(225, 0, 92))
                            embed.set_author(icon_url=message.author.avatar.url, name=f'{message.author}')
                            embed.set_footer(icon_url=message.guild.icon.url, text=f"Message sent from {message.guild.name}")
                            await self.bot.get_channel(channel['channel']).send(embed=embed)
            else:
                return None

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursor.find_one({"guild": guild.id})
        if result is not None:
            await cursor.delete_one({"guild": guild.id})