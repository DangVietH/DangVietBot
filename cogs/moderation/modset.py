import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
modb = cluster["moderation"]
cursors = modb['modlog']
cases = modb['cases']
user_case = modb['user']
cursor = cluster["moderation"]['automod']


class ModSet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, help="Modlog and case")
    async def modlog(self, ctx):
        embed = discord.Embed(title="Modlog", color=discord.Color.random(), description="Set up modlog system")
        command = self.bot.get_command("welcome")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"modlog {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @modlog.command(help="Set up channel")
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            if result is None:
                insert = {"guild": ctx.guild.id, "channel": channel.id}
                await cursors.insert_one(insert)
                await ctx.send(f"Modlog channel set to {channel.mention}")
            elif result is not None:
                await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
                await ctx.send(f"Modlog channel updated to {channel.mention}")

    @modlog.command(help="Remove modlog system if you like to")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            await cursors.delete_one(result)
            await ctx.send("Modlog system has been remove")
        else:
            await ctx.send("You don't have a Modlog channel")

    @commands.command(help="Look at your server cases", aliases=["case"])
    async def caselist(self, ctx, member: discord.Member = None):
        if member is None:
            results = await cases.find_one({"guild": ctx.guild.id})
            embed = discord.Embed(title=f"{ctx.guild.name} caselist", description=f"Total case: {results['num']}",
                                  color=discord.Color.red())
            if len(results['cases']) < 1:
                await ctx.send("Looks like all your server members are good people 🥰")
            for case in results['cases']:
                embed.add_field(name=f"Case {case['Number']}",
                                value=f"**Type:** {case['type']}\n **User:** {self.bot.get_user(int(case['user']))}\n**Mod:**{self.bot.get_user(int(case['Mod']))}\n**Reason:** {case['reason']}")
            await ctx.send(embed=embed)
        else:
            user_check = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
            if user_check is None:
                await ctx.send("Looks like a good person 🥰")
            else:
                embed = discord.Embed(title=f"{self.bot.get_user(int(user_check['user']))} cases",
                                      description=f"Total case: {user_check['total_cases']}", color=discord.Color.red())
                await ctx.send(embed=embed)

    @commands.command(help="Remove that member cases")
    @commands.has_permissions(administrator=True)
    async def forgive(self, ctx, member: discord.Member):
        user_check = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
        if user_check is None:
            await ctx.send("Looks like a good person already 🥰")
        else:
            await user_case.delete_one(user_check)
            await ctx.send("🕊 You forgive him!!")

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            results = await cases.find_one({"guild": guild.id})
            if results is None:
                insert = {"guild": guild.id, "num": 0, "cases": []}
                await cases.insert_one(insert)

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
                "anti alt": "off"
            })

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Automod commands")
    async def automod(self, ctx):
        embed = discord.Embed(title="Automod commands", color=discord.Color.random())
        command = self.bot.get_command("automod")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"automod {subcommand.name}", value=f"```{subcommand.help}```",
                                inline=False)
        await ctx.send(embed=embed)

    @automod.command(help="Turn of automod")
    @commands.has_permissions(administrator=True)
    async def end(self, ctx):
        await cursor.delete_one({"guild": ctx.guild.id})
        await ctx.send("Automod is turned off")

    @automod.command(help="Blacklist a word")
    @commands.has_permissions(administrator=True)
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
    @commands.has_permissions(administrator=True)
    async def unblacklist(self, ctx, *, word: str):
        await self.add_to_db(ctx.guild)
        word = word.lower()

        check = await cursor.find_one({"guild": ctx.guild.id, "blacklist": word})
        if check is not None:
            await cursor.update_one({{"guild": ctx.guild.id}}, {"$pull": {"blacklist": word}})
            await ctx.send(f"{word} is now unblacklisted")
        else:
            await ctx.send("Word already unblacklisted")

    @automod.command(help="Automod stats")
    @commands.has_permissions(administrator=True)
    async def stats(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        embed = discord.Embed(title=f"Automod stats of {ctx.guild.name}", color=discord.Color.from_rgb(225, 0, 92))
        value = {
            "anti spam": check['anti spam'],
            "anti invite": check['anti invite'],
            "anti link": check['anti link'],
            "anti mass mention": check['anti mass mention'],
            "anti alt": check['anti alt']
        }
        for n, v in value.items():
            embed.add_field(name=n, value=f"`{v}`", inline=False)
        await ctx.send(embed=embed)

    @automod.group(help="Enable or diable a category", invoke_without_command=True,
                   case_insensitive=True)
    @commands.has_permissions(administrator=True)
    async def toggle(self, ctx):
        embed = discord.Embed(title="Enable category", color=discord.Color.random())
        command = self.bot.get_command("automod enable")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"automod enable {subcommand.name}", value=f"```{subcommand.help}```",
                                inline=False)
        await ctx.send(embed=embed)

    @toggle.command(help="Toggle anti spam")
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti spam'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti spam": "on"}})
            await ctx.send("Anti spam is now on")
        elif check['anti spam'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti spam": "off"}})
            await ctx.send("Anti spam is now off")

    @toggle.command(help="Toggle anti invite")
    @commands.has_permissions(administrator=True)
    async def invite(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti invite'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti invite": "on"}})
            await ctx.send("Anti invite is now on")
        elif check['anti invite'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti invite": "off"}})
            await ctx.send("Anti invite is now off")

    @toggle.command(help="Toggle anti link")
    @commands.has_permissions(administrator=True)
    async def link(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti link'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti link": "on"}})
            await ctx.send("Anti link is now on")
        elif check['anti link'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti link": "off"}})
            await ctx.send("Anti link is now off")

    @toggle.command(help="Toggle anti mass mention", aliases=["ping"])
    @commands.has_permissions(administrator=True)
    async def mention(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti mass mention'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti mass mention": "on"}})
            await ctx.send("Anti mass mention is now on")
        elif check['anti mass mention'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti mass mention": "off"}})
            await ctx.send("Anti mass mention is now off")

    @toggle.command(help="Toggle anti link")
    @commands.has_permissions(administrator=True)
    async def alt(self, ctx):
        await self.add_to_db(ctx.guild)

        check = await cursor.find_one({"guild": ctx.guild.id})
        if check['anti alt'] == "off":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti mass mention": "on"}})
            await ctx.send("Anti mass mention is now on")
        elif check['anti alt'] == "on":
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"anti mass mention": "off"}})
            await ctx.send("Anti mass mention is now off")
