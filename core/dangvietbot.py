import discord
from discord.ext import commands
import os
import datetime
import re

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ['JISHAKU_RETAIN'] = "True"
os.environ['JISHAKU_FORCE_PAGINATOR'] = "True"

coglist = [
            'cogs.configuration',
            'cogs.economy',
            'cogs.entertainment',
            'cogs.info',
            'cogs.leveling',
            'cogs.mod',
            'cogs.owner',
            'cogs.rtfm',
            'cogs.utilities',
            'events.config',
            'jishaku'
]


class DangVietBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=discord.Intents.all(),
            strip_after_prefix=True,
            case_insensitive=True,
            description="One bot Many functionality",
            owner_id=860876181036335104,
            enable_debug_events=True,
            activity=discord.Game(name="d!help"),
            **kwargs
        )
        self.invite = "https://discord.com/oauth2/authorize?client_id=875589545532485682&permissions=1237420731614&scope=bot%20applications.commands"
        self.github = "https://github.com/DangVietH/DangVietBot"
        self.embed_color = discord.Color.from_rgb(225, 0, 92)

    async def setup_hook(self):
        # loading cogs
        for ext in coglist:
            try:
                await self.load_extension(ext)
                print(f"{ext} loaded")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

    async def on_ready(self):
        if not hasattr(self, "uptime"):
            self.uptime = discord.utils.utcnow()
        print(f"{self.user} is online! \nUsing discord.py {discord.__version__}\nServer {len(self.guilds)} | User: {len(self.users)}\nDevelop by DvH#9980")

    async def on_message(self, message):
        blacklist = self.mongo["custom_prefix"]["prefix"]
        if message.guild is None or message.author.bot:
            return
        if await blacklist.find_one({"id": message.author.id}):
            return
        if re.fullmatch(rf"<@!?{self.user.id}>", message.content):
            cursor = self.mongo["custom_prefix"]["prefix"]
            result = await cursor.find_one({"guild": message.guild.id})
            if result is None:
                return await message.channel.send(f"**Prefix:** `d!`")
            return await message.channel.send(f"**Prefix:** `{result['prefix']}`")

        await self.process_commands(message)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return None
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('You do not have permission to use this command')
        elif isinstance(error, commands.NotOwner):
            await ctx.send("You're not the owner of this bot")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You are missing a required argument for this command to work")
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            await ctx.send(f'⏱️ This command is on a cooldown. Use it after {str(datetime.timedelta(seconds=seconds))}')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')
        else:
            await ctx.send(error)

    async def on_guild_join(self, guild):
        cursor = self.mongo["levelling"]["disable"]
        await cursor.insert_one({"guild": guild.id})
        embed = discord.Embed(title=f"Greetings {guild.name}",
                              description=f"Thanks for adding {self.user.name} into your server! To get started type d!help!",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Note", value="I'm still WIP, so some features may be bugged or ugly.", inline=False)
        embed.add_field(name="Links",
                        value=f"[invite]({self.invite}) \n[Support Server](https://discord.gg/cnydBRnHU9)",
                        inline=False)
        embed.add_field(name="Some tips", value="Set up a modrole by using `d!modrole <role>`")
        embed.set_thumbnail(url=self.user.avatar.url)
        if guild.system_channel:
            await guild.system_channel.send(embed=embed)

    async def get_prefix(self, message):
        cursor = self.mongo["custom_prefix"]["prefix"]
        if not message.guild:
            return commands.when_mentioned_or("d!")(self, message)
        else:
            result = await cursor.find_one({"guild": message.guild.id})
            if result is None:
                return commands.when_mentioned_or("d!".lower())(self, message)
            return commands.when_mentioned_or(str(result["prefix"]).lower())(self, message)
