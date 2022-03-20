import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])

cursor = cluster['sb']['config']
msg_cursor = cluster['sb']['msg']


class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return
