import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["notification"]
cursors = db['youtube']


class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot