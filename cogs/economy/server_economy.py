import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["economy"]
serverSetup = db["server"]
econUser = db['server_user']


class ServerEconomy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Server economy commands")
    async def se(self, ctx):
        embed = discord.Embed(title="Server economy", color=discord.Color.random())
        command = self.bot.get_command("se")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"se {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @se.command(help="Create server economy")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add(self, ctx):
        check = await serverSetup.find_one({"id": ctx.guild.id})
        if check is None:
            insert = {"id": ctx.guild.id, "shop": []}
            await serverSetup.insert_one(insert)
            await ctx.send("Congratulations! Your server now has a local economy system!")
        else:
            await ctx.send("Server economy already exists!")