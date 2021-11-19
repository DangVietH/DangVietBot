import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
import datetime

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
dbs = cluster["gc"]
cursor = dbs["channel"]


class GC(commands.Cog):
    """Global chat"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Setup global chat channel")
    @commands.has_permissions(administrator=True)
    async def JoinGlobal(self, ctx, channel: discord.TextChannel):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await cursor.insert_one(insert)
            await ctx.send(f"Done! Your server is now in the global chat network")
        elif result is not None:
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"GC channel updated to {channel.mention}")

    @commands.command(help="End global chat")
    @commands.has_permissions(administrator=True)
    async def StopGlobal(self, ctx):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("Your server isn't in global chat yet")
        elif result is not None:
            await cursor.delete_one(result)
            await ctx.send("Server remove from global chat")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            result = await cursor.find_one({"channel"})


def setup(bot):
    bot.add_cog(GC(bot))
