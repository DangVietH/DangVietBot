import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]
xp = db['xp']
role = db['roles']


class Leveling(commands.Cog):
    def __init__(self, client):
        self.client = client


def setup(client):
    client.add_cog(Leveling(client))
