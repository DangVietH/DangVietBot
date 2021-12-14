from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os


cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["custom_prefix"]
cursor = db["prefix"]


class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Set custom prefix")
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx, *, prefix):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "prefix": f"{prefix}"}
            await cursor.insert_one(insert)
            await ctx.send(f"Server prefix set to `{prefix}`")
        elif result is not None:
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"prefix": f"{prefix}"}})
            await ctx.send(f"Server prefix update to `{prefix}`")

    @commands.command(help="Set prefix back to default")
    @commands.has_permissions(administrator=True)
    async def del_prefix(self, ctx):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a custom prefix yet")
        elif result is not None:
            await cursor.delete_one(result)
            await ctx.send(f"Server prefix set back to default")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startwith("dprefix"):
            result = await cursor.find_one({"guild": message.guild.id})
            if result is not None:
                await message.channel.send(f'Prefix for this server is {result["prefix"]}')
            else:
                await message.channel.send(f'Prefix for this server is d!')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursor.find_one({"guild": guild.id})
        if result is not None:
            await cursor.delete_one({"guild": guild.id})
