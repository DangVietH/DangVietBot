import discord
from discord.ext import commands, menus
from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))

db = cluster['bot']
cursor = db['blacklist']

edb = cluster["economy"]
ecursor = edb["users"]

econUser = edb['server_user']

ldb = cluster["levelling"]
levelling = ldb['member']


class TestMenu(menus.MenuPages, inherit_buttons=False):
    @menus.button('⏪')
    async def first_page(self, payload):
        await self.show_page(0)

    @menus.button('◀️')
    async def previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @menus.button('▶️')
    async def next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @menus.button('⏩')
    async def last_page(self, payload):
        max_pages = self._source.get_max_pages()
        last_page = max(max_pages - 1, 0)
        await self.show_page(last_page)

    @menus.button('⏹')
    async def on_stop(self, payload):
        self.stop()


class TestPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title="Servers")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Owner(commands.Cog):
    """Only DvH can use it"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Load a cog")
    @commands.is_owner()
    async def load(self, ctx, *, cog):
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('👌')

    @commands.command(help="Unload a cog")
    @commands.is_owner()
    async def unload(self, ctx, *, cog):
        try:
            self.bot.unload_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('👌')

    @commands.command(help="Reload a cog")
    @commands.is_owner()
    async def reload(self, ctx, *, cog):
        try:
            self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('👌')

    @commands.is_owner()
    @commands.command(help="Change the bot's status")
    async def setstatus(self, ctx, presence, *, msg):
        if presence == "game":
            await self.bot.change_presence(activity=discord.Game(name=str(msg).format(server=len(self.bot.guilds))))
        elif presence == "watch":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(msg).format(server=len(self.bot.guilds))))
        elif presence == "listen":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=str(msg).format(server=len(self.bot.guilds))))
        elif presence == "stream":
            await self.bot.change_presence(activity=discord.Streaming(name=str(msg).format(server=len(self.bot.guilds)), url="https://www.twitch.tv/dvieth"))
        else:
            await ctx.send('Invalid status')
        await ctx.message.add_reaction('👌')

    @commands.is_owner()
    @commands.command(help="See list of servers")
    async def guildlist(self, ctx):
        data = []
        for guild in self.bot.guilds:
            to_append = (f"{guild.name}", f"**Owner** {guild.owner} **Member** {guild.member_count} **ID** {guild.id}")
            data.append(to_append)
        menu = TestMenu(TestPageSource(data))
        await menu.start(ctx)

    @commands.group(help="Blacklist ppls")
    @commands.is_owner()
    async def blacklist(self, ctx):
        embed = discord.Embed(title="Blacklist", color=discord.Color.random(), description="Create reaction roles")
        command = self.bot.get_command("blacklist")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"blacklist {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @blacklist.command(help="Blacklist user")
    @commands.is_owner()
    async def user(self, ctx, user: discord.User):
        check = await cursor.find_one({"id": user.id})
        if check is None:
            users = await ecursor.find_one({"id": user.id})
            if users is not None:
                await ecursor.delete_one({"id": user.id})

            if await levelling.find_one({"user": user.id}) is not None:
                await levelling.delete_one({"user": user.id})

            if await econUser.find_one({"user": user.id}) is not None:
                await econUser.delete_one({"user": user.id})
            await user.send("You have been blacklisted")

            for guild in self.bot.guilds:
                if guild.owner.id == user.id:
                    await guild.system_channel.send("Leave this server because the owner is blacklisted")

            await cursor.insert_one({"id": user.id})
            await ctx.send("Blacklist user successfully")
        else:
            await ctx.send("User already blacklist")

    @commands.command(help="unBlacklist user")
    @commands.is_owner()
    async def unblacklist(self, ctx, user: discord.User):
        await cursor.delete_one({"id": user.id})
        await ctx.send("Unblacklist user successfully")