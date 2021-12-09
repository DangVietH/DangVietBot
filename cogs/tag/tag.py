import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["tag"]
cursor = db["tags"]


class Tag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot