import discord
from discord.ext import commands, menus
from utils.menuUtils import MenuPages
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
import contextlib
import io
import textwrap
from traceback import format_exception

cluster = AsyncIOMotorClient(config_var['mango_link'])

cursor = cluster['bot']['blacklist']

ecursor = cluster["economy"]["users"]

levelling = cluster["levelling"]['member']


class EvalPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        return f"```py\n{entries}\n```\nPage {menu.current_page + 1}/{self.get_max_pages()}"


class Owner(commands.Cog):
    """Only DvH can use it"""
    def __init__(self, bot):
        self.bot = bot

    def clean_code(self, code):
        if code.startswith('```') and code.endswith('```'):
            return '\n'.join(code.split('\n')[1:-3])
        else:
            return code

    @commands.command(help="Load a cog")
    @commands.is_owner()
    async def load(self, ctx, *, cog=None):
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'⬆️`{cog}`')

    @commands.command(help="Unload a cog")
    @commands.is_owner()
    async def unload(self, ctx, *, cog=None):
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'⬇️`{cog}`')

    @commands.command(help="Reload a cog")
    @commands.is_owner()
    async def reload(self, ctx, *, cog=None):
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'🔁`{cog}`')

    @commands.is_owner()
    @commands.command(help="Change the bot status")
    async def setstatus(self, ctx, presence, *, msg):
        if presence == "game":
            await self.bot.change_presence(activity=discord.Game(name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        elif presence == "watch":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        elif presence == "listen":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        elif presence == "stream":
            await self.bot.change_presence(activity=discord.Streaming(name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users)), url="https://www.twitch.tv/dvieth"))
        else:
            await ctx.send('Invalid status')
        await ctx.message.add_reaction('👌')
    
    @commands.command(help="Toggles on and off a command")
    @commands.is_owner()
    async def cmd_toggle(self, ctx, command: str):
        command = self.bot.get_command(command)
        if not command.enabled:
            command.enabled = True
            await ctx.reply(F"Enabled {command.name} command")
        else:
            command.enabled = False
            await ctx.reply(F"Disabled {command.name} command.")

    @commands.command(help="Run code")
    @commands.is_owner()
    async def eval(self, ctx, *, code):
        code = self.clean_code(code)
        variables = {
            'discord': discord,
            'bot': self.bot,
            'commands': commands,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(f"async def func():\n{textwrap.indent(code, '    ')}", variables)
                result = f"{stdout.getvalue()}"
        except Exception as e:
            result = "".join(format_exception(type(e), e, e.__traceback__))

        page = MenuPages(source=EvalPageSource([result[i: i + 2000] for i in range(0, len(result), 2000)]), clear_reactions_after=True)
        await page.start(ctx)

    @commands.group(help="Blacklist ppls")
    @commands.is_owner()
    async def blacklist(self, ctx, user: discord.User, *, reason):
        check = await cursor.find_one({"id": user.id})
        if check is not None:
            return await ctx.send("User is already blacklisted")
        await user.send(f"You have been **BLACKLISTED** from DangVietBot for: **{reason}**")
        await cursor.insert_one({"id": user.id})
        for guild in self.bot.guilds:
            if guild.owner.id == user.id:
                await guild.system_channel.send("Leave this server because the owner is blacklisted")
                await guild.leave()

        await ctx.send("Blacklist user successfully")

    @commands.command(help="unBlacklist user")
    @commands.is_owner()
    async def unblacklist(self, ctx, user: discord.User):
        await cursor.delete_one({"id": user.id})
        await ctx.send("Unblacklist user successfully")
        await user.send(f"You have been unblacklisted")