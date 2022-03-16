import discord
from discord.ext import commands, menus
from utils.menuUtils import ViewMenuPages
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
modb = cluster["moderation"]
cursors = modb['modlog']
cases = modb['cases']
user_case = modb['user']


class GuildLeaderboardPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url=menu.ctx.author.guild.icon.url,
            name=f"Leaderboard of {menu.ctx.author.guild.name}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class ModUtils(commands.Cog):
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

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            results = await cases.find_one({"guild": guild.id})
            if results is None:
                insert = {"guild": guild.id, "num": 0, "cases": []}
                await cases.insert_one(insert)
