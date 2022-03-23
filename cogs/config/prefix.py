from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
from cogs.config.configuration import ConfigurationBase

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["custom_prefix"]["prefix"]


class Prefix(ConfigurationBase):
    @commands.group(invoke_without_command=True, case_insensitive=True, help="Custom prefix setup")
    async def prefix(self, ctx):
        _cmd = self.bot.get_command("help")
        await _cmd(ctx, command='prefix')

    @prefix.command(help="Set custom prefix")
    @commands.has_permissions(manage_guild=True)
    async def set(self, ctx, *, prefixes):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "prefix": f"{prefixes}"}
            await cursor.insert_one(insert)
            await ctx.send(f"Server prefix set to `{prefixes}`")
        elif result is not None:
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"prefix": f"{prefixes}"}})
            await ctx.send(f"Server prefix update to `{prefixes}`")

    @prefix.command(help="Set prefix back to default")
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a custom prefix yet")
        elif result is not None:
            await cursor.delete_one(result)
            await ctx.send(f"Server prefix set back to default")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursor.find_one({"guild": guild.id})
        if result is not None:
            await cursor.delete_one({"guild": guild.id})
