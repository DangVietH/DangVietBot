import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var


cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["economy"]
cursor = db["users"]
company = db["company"]


class Business(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

