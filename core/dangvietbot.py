import discord
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
import random
import datetime
from utils.configs import config_var
from core.help import CustomHelp

cluster = AsyncIOMotorClient(config_var["mango_link"])
timer = cluster["timer"]
modtime = timer['mod']
reminder = timer['remind']
giveaway = timer['giveaway']

coglist = [
            'cogs.audio',
            'cogs.economy',
            'cogs.entertainment',
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
            activity=discord.Game(name="d!help"),
            **kwargs
        )

    def run(self):
        super().run(config_var['token'], reconnect=True)

    async def setup_hook(self):
        self.time_checker.start()
        for ext in coglist:
            try:
                await self.load_extension(ext)
                print(f"{ext} loaded")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")

    async def on_ready(self):
        print(f"{self.user} is online! \nUsing discord.py {discord.__version__} \nDevelop by DvH#9980")

    async def on_message(self, message):
        if message.author.bot:
            return
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

    @tasks.loop(seconds=10)
    async def time_checker(self):
        # until i figure out about the asyncio change for cog
        try:
            # mod
            all_timer = modtime.find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    if x['type'] == "mute":
                        server = self.bot.get_guild(int(x['guild']))
                        member = server.get_member(int(x['user']))
                        mutedRole = server.get_role(int(x['role']))
                        await member.remove_roles(mutedRole)

                        await modtime.delete_one({"user": member.id})
                    elif x['type'] == "ban":
                        server = self.bot.get_guild(int(x['guild']))
                        user = self.bot.get_user(int(x['user']))
                        await server.unban(user)

                        await modtime.delete_one({"user": user.id})
                else:
                    pass
            # reminder
            all_timer = reminder.find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    user = self.bot.get_user(x['user'])
                    await user.send(f"**Reminder:** {x['reason']}")
                    await reminder.delete_one({"user": user.id})
                else:
                    pass
            # giveaway
            all_giv = giveaway.find({})
            current_time = datetime.datetime.now()
            async for x in all_giv:
                if current_time >= x['time']:
                    msg_id = x['message_id']
                    channel = self.bot.get_channel(x['channel'])
                    msg = await self.bot.fetch_message(msg_id)
                    users = await msg.reactions[0].users().flatten()
                    users.pop(users.index(self.bot.user))

                    winner = random.choice(users)
                    if winner is None:
                        return await channel.send("No one has entered the giveaway. Maybe next time")
                    embed = discord.Embed(color=discord.Color.red(), title="🥳 THE GIVEAWAY HAS ENDED!")
                    embed.add_field(name=f"🎉 Prize: {x['prize']}",
                                    value=f'🥳 **Winner**: {winner.mention}\n 🎫 **Number of Entrants**: {len(users)}',
                                    inline=False)
                    embed.set_footer(text='Thanks for entering the giveaway!')
                    await msg.edit(embed=embed)
                    await giveaway.delete_one({'message_id': msg_id})
        except Exception as e:
            print(e)

    async def get_prefix(self, message):
        cursor = cluster["custom_prefix"]["prefix"]
        if not message.guild:
            return commands.when_mentioned_or("d!")(self, message)
        else:
            result = await cursor.find_one({"guild": message.guild.id})
            if result is not None:
                return commands.when_mentioned_or(str(result["prefix"]))(self, message)
            else:
                return commands.when_mentioned_or("d!")(self, message)
