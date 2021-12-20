import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["economy"]
serverSetup = db["server"]
econUser = db['server_user']

ECON_NOT_ENABLED = "Server economy not enabled"
NO_ACCOUNT = "You don't have an economy account. Please use the se create_account command to create one"


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

    @se.command(help="Create server economy system")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def create(self, ctx):
        check = await serverSetup.find_one({"id": ctx.guild.id})
        if check is None:
            insert = {"id": ctx.guild.id, "shop": [], "rob": "True", "emoji": "<:DHBuck:901485795410599988>"}
            await serverSetup.insert_one(insert)
            await ctx.send("Congratulations! Your server now has a local economy system!")
        else:
            await ctx.send("Server economy already exists!")

    @se.command(help="Set server economy emoji")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def emote(self, ctx, *, emoji: str):
        check = await serverSetup.find_one({"id": ctx.guild.id})
        if check is None:
            await ctx.send(ECON_NOT_ENABLED)
        else:
            await check.update_one({"id": ctx.guild.id}, {"$set": {"emoji": emoji}})

    @se.command(help="Create server economy system")
    @commands.guild_only()
    async def create_account(self, ctx):
        is_econ_enable = await serverSetup.find_one({"id": ctx.guild.id})
        if is_econ_enable is None:
            await ctx.send(ECON_NOT_ENABLED)
        else:
            check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
            if check is None:
                await econUser.insert_one(
                    {"guild": ctx.guild.id, "user": ctx.author.id, "wallet": 0, "bank": 0, "inventory": []})
                await ctx.send("Account created successfully")
            else:
                await ctx.send("You already have an account")

    @se.command(help="View your server balance")
    @commands.guild_only()
    async def bal(self, ctx):
        is_econ_enable = await serverSetup.find_one({"id": ctx.guild.id})
        if is_econ_enable is None:
            await ctx.send(ECON_NOT_ENABLED)
        else:
            check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
            if check is None:
                await ctx.send(NO_ACCOUNT)
            else:
                wallet = check['wallet']
                bank = check['bank']
                balance = wallet + bank
                embed = discord.Embed(description=f"**Total:** {is_econ_enable['emoji']} {balance}",
                                      color=discord.Color.blue())
                embed.set_author(
                    icon_url=ctx.author.avatar.url,
                    name=f"{ctx.author} balance")
                embed.add_field(name="Wallet", value=f"{is_econ_enable['emoji']} {wallet}", inline=False)
                embed.add_field(name="Bank", value=f"{is_econ_enable['emoji']} {bank}", inline=False)
                await ctx.send(embed=embed)

    @se.command(help="Beg money")
    @commands.guild_only()
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def beg(self, ctx):
        is_econ_enable = await serverSetup.find_one({"id": ctx.guild.id})
        if is_econ_enable is None:
            await ctx.send(ECON_NOT_ENABLED)
        else:
            check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
            if check is None:
                await ctx.send(NO_ACCOUNT)
            else:
                random_money = random.randint(1, 1000)
                await econUser.update_one({"id": ctx.author.id}, {"$inc": {"wallet": random_money}})
                await ctx.send(f"Someone gave you {is_econ_enable['emoji']} {random_money}")