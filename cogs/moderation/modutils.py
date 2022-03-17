import nextcord as discord
from nextcord.ext import commands, menus
from utils.menuUtils import ViewMenuPages
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
modb = cluster["moderation"]
cursors = modb['modlog']
cases = modb['cases']
user_case = modb['user']


class GuildCasePageSource(menus.ListPageSource):
    def __init__(self, casenum, data):
        self.casenum = casenum
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.red(), title=f"List of cases in {menu.ctx.author.guild.name}", description=f"**Total case:** {self.casenum}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class UserCasePageSource(menus.ListPageSource):
    def __init__(self, member, casenum, data):
        self.member = member
        self.casenum = casenum
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.red(), title=f"List of cases in {menu.ctx.author.guild.name}", description=f"**Total case:** {self.casenum}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class ModUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_to_db(self, guild):
        results = await cases.find_one({"guild": guild.id})
        if results is None:
            insert = {"guild": guild.id, "num": 0, "cases": []}
            await cases.insert_one(insert)

    @commands.group(invoke_without_command=True, help="Modlog and case")
    async def modlog(self, ctx):
        await self.add_to_db(ctx.guild)
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
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await cursors.insert_one(insert)
            await ctx.send(f"Modlog channel set to {channel.mention}")
            return
        await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
        await ctx.send(f"Modlog channel updated to {channel.mention}")

    @modlog.command(help="Remove modlog system if you like to")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a Modlog channel")
        await cursors.delete_one(result)
        await ctx.send("Modlog system has been remove")

    @commands.command(help="Look at server cases", aliases=["case"])
    @commands.guild_only()
    async def caselist(self, ctx):
        await self.add_to_db(ctx.guild)
        results = await cases.find_one({"guild": ctx.guild.id})
        gdata = []
        if len(results['cases']) < 1:
            return await ctx.send("Looks like all your server members are good people! Good job!")
        for case in results['cases']:
            gdata.append((f"Case {case['Number']}",
                          f"**Type:** {case['type']}\n **User:** {self.bot.get_user(int(case['user']))}\n**Mod:**{self.bot.get_user(int(case['Mod']))}\n**Reason:** {case['reason']}"))
        page = ViewMenuPages(source=GuildCasePageSource(results['num'], gdata), disable_buttons_after=True, ctx=ctx)
        await page.start(ctx)

    @commands.command(help="Look at user cases", aliases=["ucase"])
    @commands.guild_only()
    async def usercase(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        udata = []
        user_check = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
        results = await cases.find_one({"guild": ctx.guild.id})
        if user_check is None:
            return await ctx.send("Looks like a good person 🥰")
        for case in results['cases']:
            if member.id == int(case['user']):
                udata.append((f"Case {case['Number']}",
                              f"**Type:** {case['type']}\n**Mod:**{self.bot.get_user(int(case['Mod']))}\n**Reason:** {case['reason']}"))

        page = ViewMenuPages(source=UserCasePageSource(member, user_check['total_cases'], udata),
                             disable_buttons_after=True, ctx=ctx)
        await page.start(ctx)