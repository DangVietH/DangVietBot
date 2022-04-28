import contextlib
import io
import textwrap
import traceback

import discord
from discord.ext import commands


class Owner(commands.Cog):
    """Only DvH can use it"""
    emoji = "👑"

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
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'⬆️`{cog}`')

    @commands.command(help="Unload a cog")
    @commands.is_owner()
    async def unload(self, ctx, *, cog=None):
        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send(f'⬇️`{cog}`')

    @commands.command(help="Reload a cog")
    @commands.is_owner()
    async def reload(self, ctx, *, cog=None):
        try:
            await self.bot.reload_extension(cog)
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
    async def cmd_toggle(self, ctx, *, command: str):
        command = self.bot.get_command(command)
        if not command.enabled:
            command.enabled = True
            await ctx.reply(F"Enabled {command.name} command")
        else:
            command.enabled = False
            await ctx.reply(F"Disabled {command.name} command.")

    @commands.command(help="Shutdown the bot")
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send('Shutting down...')
        await self.bot.close()

    @commands.command(help="Run code", aliases=['e'])
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
                exec(f"async def func():\n{textwrap.indent(code, '  ')}", variables)
                result = f"{stdout.getvalue()}"
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            await ctx.send(result)

    @commands.group(help="Blacklist ppls")
    @commands.is_owner()
    async def blacklist(self, ctx, user: discord.User, *, reason):
        check = await self.bot.mongo['bot']['blacklist'].find_one({"id": user.id})
        if check is not None:
            return await ctx.send("User is already blacklisted")
        await user.send(f"You have been **BLACKLISTED** from DangVietBot for: **{reason}**")
        await self.bot.mongo['bot']['blacklist'].insert_one({"id": user.id})
        if await self.bot.mongo["economy"]["users"].insert_one({"id": user.id}):
            await self.bot.mongo["economy"]["users"].delete_one({"id": user.id})
        async for x in self.bot.mongo["levelling"]['member'].find({"user": user.id}):
            await self.bot.mongo["levelling"]['member'].delete_one(x)
        for guild in self.bot.guilds:
            if guild.owner.id == user.id:
                await guild.system_channel.send("Leave this server because the owner is blacklisted")
                await guild.leave()

        await ctx.send("Blacklist user successfully")

    @commands.command(help="unBlacklist user")
    @commands.is_owner()
    async def unblacklist(self, ctx, user: discord.User):
        await self.bot.mongo['bot']['blacklist'].delete_one({"id": user.id})
        await ctx.send("Unblacklist user successfully")
        await user.send(f"You have been unblacklisted")