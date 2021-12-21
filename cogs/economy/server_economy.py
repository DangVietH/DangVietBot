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

    async def server_econ_create(self, guild):
        check = await serverSetup.find_one({"id": guild.id})
        if check is None:
            insert = {"id": guild.id, "shop": [], "rob": "True", "emoji": "<:DHBuck:901485795410599988>", "starting_wallet": 0, "role": [], "rolenum": []}
            await serverSetup.insert_one(insert)

    async def open_account(self, user):
        users = await econUser.find_one({"guild": user.guild.id, "user": user.id})
        servercheck = await serverSetup.find_one({"id": user.guild.id})
        if users is None:
            insert = {"guild": user.guild.id, "user": user.id, "wallet": int(servercheck['starting_wallet']), "bank": 0, "inventory": []}
            await econUser.insert_one(insert)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Server economy commands")
    async def se(self, ctx):
        embed = discord.Embed(title="Server economy", color=discord.Color.random())
        command = self.bot.get_command("se")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"se {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @se.command(help="Set server economy emoji")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def emote(self, ctx, *, emoji: str):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        await serverSetup.update_one({"id": ctx.guild.id}, {"$set": {"emoji": emoji}})
        await ctx.send(f"Economy emoji is now {emoji}")

    @se.command(help="View your server balance")
    @commands.guild_only()
    async def bal(self, ctx):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
        severSys = await serverSetup.find_one({"id": ctx.guild.id})

        wallet = check['wallet']
        bank = check['bank']
        balance = wallet + bank
        embed = discord.Embed(description=f"**Total:** {severSys['emoji']} {balance}",
                              color=discord.Color.blue())
        embed.set_author(
            icon_url=ctx.author.avatar.url,
            name=f"{ctx.author} balance")
        embed.add_field(name="Wallet", value=f"{severSys['emoji']} {wallet}", inline=False)
        embed.add_field(name="Bank", value=f"{severSys['emoji']} {bank}", inline=False)
        await ctx.send(embed=embed)

    @se.command(help="Beg money")
    @commands.guild_only()
    @commands.cooldown(1, 7200, commands.BucketType.guild)
    async def beg(self, ctx):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        severSys = await serverSetup.find_one({"id": ctx.guild.id})

        random_money = random.randint(1, 1000)
        await econUser.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": random_money}})
        await ctx.send(f"Someone gave you {severSys['emoji']} {random_money}")