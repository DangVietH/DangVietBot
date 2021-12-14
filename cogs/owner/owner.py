import discord
from discord.ext import commands, menus


class TestMenu(menus.Menu):
    async def send_initial_message(self, ctx, channel):
        return await channel.send('Hello there')

    @menus.button('\N{THUMBS UP SIGN}')
    async def on_thumbs_up(self, payload):
        await self.message.edit(content='ok')

    @menus.button('\N{THUMBS DOWN SIGN}')
    async def on_thumbs_down(self, payload):
        await self.message.edit(content=f"What")

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f')
    async def on_stop(self, payload):
        self.stop()


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
        menu = TestMenu()
        await menu.start(ctx)