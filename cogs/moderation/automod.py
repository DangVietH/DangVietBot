import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
cursor = cluster["moderation"]['automod']


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_to_db(self, guild):
        check = await cursor.find_one({"guild": guild.id})
        if check is None:
            await cursor.insert_one({
                "guild": guild.id,
                "blacklist": [],
                "anti spam": "off",
                "anti invite": "off",
                "anti link": "off",
                "anti mass mention": "off",
                "anti raid": "off"
            })

    @commands.group(invoke_without_command=True, case_insensitive=True, help="FireCoin commands")
    async def automod(self, ctx):
        embed = discord.Embed(title="Automod commands", color=discord.Color.random())
        command = self.bot.get_command("automod")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"automod {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @automod.command(help="Blacklist a word")
    async def blacklist(self, ctx, *, word: str):
        await self.add_to_db(ctx.guild)
        word = word.lower()

        check = await cursor.find_one({"guild": ctx.guild.id, "blacklist": word})
        if check is None:
            await cursor.update_one({{"guild": ctx.guild.id}}, {"$push": {"blacklist": word}})
            await ctx.send(f"{word} is now blacklisted")
        else:
            await ctx.send("Word already blacklisted")

    @automod.command(help="Unblacklist a word")
    async def unblacklist(self, ctx, *, word: str):
        await self.add_to_db(ctx.guild)
        word = word.lower()

        check = await cursor.find_one({"guild": ctx.guild.id, "blacklist": word})
        if check is not None:
            await cursor.update_one({{"guild": ctx.guild.id}}, {"$pull": {"blacklist": word}})
            await ctx.send(f"{word} is now unblacklisted")
        else:
            await ctx.send("Word already unblacklisted")

    @automod.group(help="Enable or diable a category", aliase=['disable', "toggle"], invoke_without_command=True,
                   case_insensitive=True)
    async def enable(self, ctx):
        embed = discord.Embed(title="Enable category", color=discord.Color.random())
        command = self.bot.get_command("automod enable")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"automod enable {subcommand.name}", value=f"```{subcommand.help}```",
                                inline=False)
        await ctx.send(embed=embed)

    @enable.command(help="Toggle anti spam")
    async def spam(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti spam'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti spam": "on"}})
            await ctx.send("Anti spam is now on")
        elif check['anti spam'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti spam": "off"}})
            await ctx.send("Anti spam is now off")

    @enable.command(help="Toggle anti invite")
    async def invite(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti invite'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti invite": "on"}})
            await ctx.send("Anti invite is now on")
        elif check['anti invite'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti invite": "off"}})
            await ctx.send("Anti invite is now off")

    @enable.command(help="Toggle anti link")
    async def link(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti link'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti link": "on"}})
            await ctx.send("Anti link is now on")
        elif check['anti link'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti link": "off"}})
            await ctx.send("Anti link is now off")

    @enable.command(help="Toggle anti mass mention", aliases=["ping"])
    async def mention(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti mass mention'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti mass mention": "on"}})
            await ctx.send("Anti mass mention is now on")
        elif check['anti mass mention'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti mass mention": "off"}})
            await ctx.send("Anti mass mention is now off")

    @enable.command(help="Toggle anti link")
    async def raid(self, ctx):
        await self.add_to_db(ctx.guild)

        await ctx.send("Coming soon!")