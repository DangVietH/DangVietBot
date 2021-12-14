import discord
from discord.ext import commands, menus


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
        super().__init__(data, per_page=2)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title="🏆 Test")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
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
    @commands.command(help="Test my menus skills")
    async def tmenus(self, ctx):
        data = [
            ("Black", "#000000"),
            ("Blue", "#0000FF"),
            ("Brown", "#A52A2A"),
            ("Green", "#00FF00"),
            ("Grey", "#808080"),
            ("Orange", "#FFA500"),
            ("Pink", "#FFC0CB"),
            ("Purple", "#800080"),
            ("Red", "#FF0000"),
            ("White", "#FFFFFF"),
            ("Yellow", "#FFFF00"),
        ]
        menu = TestMenu(TestPageSource(data), per_page=2)
        await menu.start(ctx)