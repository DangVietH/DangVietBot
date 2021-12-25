from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_data

cluster = AsyncIOMotorClient(config_data["mango_link"])
db = cluster["custom_prefix"]
cursor = db["prefix"]


class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursor.find_one({"guild": guild.id})
        if result is not None:
            await cursor.delete_one({"guild": guild.id})
