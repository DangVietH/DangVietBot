import discord
from discord.ext import commands
from utils.menuUtils import MenuPages, DefaultPageSource
from cogs.info.help import CustomHelp
import datetime
import io
import os
import inspect


class Info(commands.Cog):
    emoji = "📋"

    def __init__(self, bot):
        self.bot = bot
        bot.help_command = CustomHelp()
        bot.help_command.cog = self

    @commands.command(aliases=['src'], help="Shows the source code for a command")
    async def source(self, ctx, *, command=None):
        source_url = "https://github.com/DangVietH/DangVietBot"
        if command is None:
            return await ctx.send(f"<{source_url}>")

        command = self.bot.get_command(command)
        if not command:
            return await ctx.send("That command doesn't exist!'")

        src = command.callback.__code__
        filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)

        location = os.path.relpath(filename).replace("\\", "/")

        await ctx.send(f"<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>")

    @commands.command(help="See bot latency")
    async def ping(self, ctx):
        await ctx.send(f"🏓**Pong!** My latency is {round(self.bot.latency * 1000)}ms")

    @commands.command(help="See user info", aliases=['userinfo', 'ui'])
    async def whois(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        if user.activity is not None:
            activity = user.activity.name
        else:
            activity = None

        embed = discord.Embed(timestamp=ctx.message.created_at, color=user.color)
        embed.set_author(name=f"{user}", icon_url=user.display_avatar.url)
        embed.add_field(name="Nick", value=user.nick, inline=False)
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Status", value=user.status)
        embed.add_field(name="In voice", value=None if not user.voice else user.voice.channel)
        embed.add_field(name="Activity", value=activity)
        embed.add_field(name="Top role", value=user.top_role.mention)
        embed.add_field(name="Bot", value=user.bot)
        embed.add_field(name="Create at", value=f"<t:{int(user.created_at.timestamp())}:R>")
        embed.add_field(name="Join at", value=f"<t:{int(user.joined_at.timestamp())}:R>")
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(help="Get user avatar")
    async def avatar(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        resp = await self.bot.session.get(user.display_avatar.url)
        await ctx.send(file=discord.File(io.BytesIO(await resp.read()), f"avatar.png"))

    @commands.command(help="Server information")
    async def serverinfo(self, ctx):
        role_count = len(ctx.guild.roles)
        emoji_count = len(ctx.guild.emojis)
        embed = discord.Embed(title=f"{ctx.guild.name}", color=self.bot.embed_color, timestamp=ctx.message.created_at)
        embed.add_field(name="ID", value=f"{ctx.guild.id}")
        embed.add_field(name="Owner", value=f"{ctx.guild.owner}")
        embed.add_field(name="Member count", value=f"{ctx.guild.member_count}")
        embed.add_field(name="Verification Level", value=f"{ctx.guild.verification_level}")
        embed.add_field(name="Highest role", value=f"{ctx.guild.roles[-1]}")
        embed.add_field(name="Number of roles", value=f"{role_count}")
        embed.add_field(name="Number of emojis", value=f"{emoji_count}")
        embed.add_field(name="Create on", value=f"<t:{int(ctx.guild.created_at.timestamp())}:R>")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(help="Bot information", aliases=['botinfo', 'stats'])
    async def about(self, ctx):
        lob = []
        for x in self.bot.users:
            if x.bot:
                lob.append(x)
        embed = discord.Embed(title="Bot Information", color=self.bot.embed_color)
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(name="Developer", value=f"DvH#9980")
        embed.add_field(name="Version", value="v0.9.5-alpha")
        embed.add_field(name="Written in", value="Python 3.10.1")
        embed.add_field(name="Library", value=f"[discord.py {discord.__version__}](https://github.com/Rapptz/discord.py)")
        embed.add_field(name="Uptime", value=f"<t:{int(datetime.datetime.timestamp(self.bot.uptime))}:R>")
        embed.add_field(name="Create at", value=f"<t:{int(self.bot.user.created_at.timestamp())}:R>")
        embed.add_field(name="Command's", value=f"{len(self.bot.commands)}")
        embed.add_field(name="Server's", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="User's", value=f"{len(self.bot.users)} total\n{len(lob)} bots")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Invite', url=self.bot.invite))
        view.add_item(discord.ui.Button(label='Support server', url='https://discord.gg/cnydBRnHU9'))
        view.add_item(discord.ui.Button(label='Github', url='https://github.com/DangVietH/DangVietBot'))
        await ctx.send(embed=embed, view=view)

    @commands.command(help="Show bot uptime")
    async def uptime(self, ctx):
        await ctx.send(f"<t:{int(datetime.datetime.timestamp(self.bot.uptime))}:R>")

    @commands.command(help="Invite the bot")
    async def invite(self, ctx):
        embed = discord.Embed(title='Click here to Invite Me', url=self.bot.invite, description="**Default Prefix:** d!", color=self.bot.embed_color)
        await ctx.send(embed=embed)

    @commands.command(help="See list of servers")
    @commands.is_owner()
    async def guildlist(self, ctx):
        data = []
        for guild in self.bot.guilds:
            to_append = (f"{guild.name}", f"**Owner** {guild.owner} **Member** {guild.member_count} **ID** {guild.id}")
            data.append(to_append)
        menu = MenuPages(DefaultPageSource("Servers", data), ctx)
        await menu.start()