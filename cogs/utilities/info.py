import discord
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="See bot latency")
    async def ping(self, ctx):
        await ctx.send(f"🏓**Pong!** My latency is {round(self.bot.latency * 1000)}ms")

    @commands.command(help="See user info")
    async def whois(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        if user.activity is not None:
            activity = user.activity.name
        else:
            activity = None

        voice_state = None if not user.voice else user.voice.channel

        hypesquad_class = str(user.public_flags.all()).replace('[<UserFlags.', '').replace('>]', '').replace('_', ' ').replace(':', '').title()

        # Remove digits from string
        hypesquad_class = ''.join([i for i in hypesquad_class if not i.isdigit()])

        embed = discord.Embed(title=f"{user}", timestamp=ctx.message.created_at, color=user.color)
        embed.add_field(name="Nick", value=user.nick, inline=False)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Status", value=user.status, inline=True)
        embed.add_field(name="In voice", value=voice_state, inline=True)
        embed.add_field(name="Activity", value=activity, inline=True)
        embed.add_field(name="Top role", value=user.top_role.mention, inline=True)
        embed.add_field(name="Bot", value=user.bot, inline=True)
        embed.add_field(name="Badges", value=hypesquad_class, inline=False)
        embed.add_field(name="Create at", value=user.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S'), inline=True)
        embed.add_field(name="Join at", value=user.joined_at.__format__('%A, %d. %B %Y @ %H:%M:%S'), inline=True)
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(help="Get user avatar")
    async def avatar(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        await ctx.send(user.avatar.url)

    @commands.command(help="Server information")
    async def serverinfo(self, ctx):
        role_count = len(ctx.guild.roles)
        emoji_count = len(ctx.guild.emojis)
        embed = discord.Embed(title=f"{ctx.guild.name}", color=discord.Color.random(), timestamp=ctx.message.created_at)
        embed.add_field(name="ID", value=f"{ctx.guild.id}")
        embed.add_field(name="Owner", value=f"{ctx.guild.owner}")
        embed.add_field(name="Member count", value=f"{ctx.guild.member_count}")
        embed.add_field(name="Region", value=f"{ctx.guild.region}")
        embed.add_field(name="Verification Level", value=f"{ctx.guild.verification_level}")
        embed.add_field(name="Highest role", value=f"{ctx.guild.roles[-1]}")
        embed.add_field(name="Number of roles", value=f"{role_count}")
        embed.add_field(name="Number of emojis", value=f"{emoji_count}")
        embed.add_field(name="Create on", value=f"{ctx.guild.created_at.__format__('%A, %d. %B %Y @ %H:%M:%S')}")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(help="Bot information")
    async def about(self, ctx):
        embed = discord.Embed(title="Bot information", color=discord.Color.random())
        embed.add_field(name="Developer", value=f"! DvH#9980")
        embed.add_field(name="Version", value="0.6.0")
        embed.add_field(name="Written in", value="Python 3.9.6")
        embed.add_field(name="Library", value="[pycord 2.0](https://github.com/Pycord-Development/pycord)")
        embed.add_field(name="Create at", value="8/13/2021")
        embed.add_field(name="Command's", value=f"{len(self.bot.commands)}")
        embed.add_field(name="Server's", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="User's", value=f"{len(self.bot.users)}")
        await ctx.send(embed=embed)

    @commands.command(help="Invite the bot")
    async def invite(self, ctx):
        embed = discord.Embed(title='Invite?', description="[here](https://discord.com/api/oauth2/authorize?client_id=875589545532485682&permissions=8&scope=bot%20applications.commands)")
        await ctx.send(embed=embed)
