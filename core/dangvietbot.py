import discord
from discord.ext import commands, ipc
from motor.motor_asyncio import AsyncIOMotorClient

import datetime
from utils.configs import config_var
from core.help import CustomHelp

coglist = [
            'cogs.audio',
            'cogs.economy',
            'cogs.entertainment',
            'cogs.ipc',
            'cogs.leveling',
            'cogs.moderation',
            'cogs.owner',
            'cogs.rtfm',
            'cogs.settings',
            'cogs.utilities',
            'jishaku']


class DangVietBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=discord.Intents.all(),
            strip_after_prefix=True,
            case_insensitive=True,
            help_command=CustomHelp(),
            description="One bot Many functionality",
            owner_id=860876181036335104,
            enable_debug_events=True,
            activity=discord.Streaming(name="d!help", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            **kwargs
        )
        self.mongo = config_var['mango_link']
        self.ipc = ipc.Server(self, secret_key=config_var['ipc'])

        # loading cogs
        for ext in coglist:
            try:
                self.load_extension(ext)
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

    def run(self):
        super().run(config_var['token'], reconnect=True)

    async def on_ready(self):
        print(f"{self.user} is online! \nUsing nextcord {discord.__version__} \nDevelop by DvH#9980")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return None
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('You do not have permission to use this command')
        elif isinstance(error, commands.NotOwner):
            await ctx.send("You're not the owner of the bot")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You are missing a required argument for this command to work")
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            await ctx.send(f'⏱️ This command is on a cooldown. Use it after {str(datetime.timedelta(seconds=seconds))}')
        else:
            await ctx.send(error)

    async def on_guild_join(self, guild):
        embed = discord.Embed(title=f"Greetings {guild.name}",
                              description=f"Thanks for adding {self.user.name} into your server! To get started type d!help!",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Note", value="I'm still WIP, so some features may be bugged or ugly.", inline=False)
        embed.add_field(name="Links",
                        value="[invite](https://discord.com/oauth2/authorize?client_id=875589545532485682&permissions=549755813887&scope=bot%20applications.commands) \n[Support Server](https://discord.gg/cnydBRnHU9)",
                        inline=False)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/avatars/875589545532485682/a5123a4fa15dad3beca44144d6749189.png?size=1024")
        await guild.system_channel.send(embed=embed)

    async def get_prefix(self, message):
        cluster = AsyncIOMotorClient(self.mongo)
        cursor = cluster["custom_prefix"]["prefix"]
        if not message.guild:
            return commands.when_mentioned_or("d!")(self, message)
        else:
            result = await cursor.find_one({"guild": message.guild.id})
            if result is not None:
                return commands.when_mentioned_or(str(result["prefix"]))(self, message)
            else:
                return commands.when_mentioned_or("d!")(self, message)

    async def on_ipc_error(self, endpoint, error):
        print(endpoint, "raised", error)
