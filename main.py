import nextcord as discord
from nextcord.ext import commands, menus
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import os
from utils.menuUtils import MenuButtons


config_var = {
    "token": os.environ.get("token"),
    "mango_link": os.environ.get("mango_link"),
    "reddit_pass": os.environ.get("reddit_pass"),
    "reddit_secret": os.environ.get("reddit_secret")
}


class HelpPageSource(menus.ListPageSource):
    def __init__(self, help_command, data):
        self.help_command = help_command
        super().__init__(data, per_page=5)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.from_rgb(225, 0, 92),
                              title=f"DHB Commands",
                              description=f'Use {self.help_command.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.help_command.context.clean_prefix}help Economy'
                              )
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return f'{self.context.clean_prefix}{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        data = []

        for cog, command in mapping.items():
            name = "No Category" if cog is None else cog.qualified_name
            filtered = await self.filter_commands(command, sort=True)
            if filtered:
                value = "\u2002".join(
                    f"`{self.context.clean_prefix}{c.name}`" for c in filtered)
                if cog and cog.description:
                    value = f"{cog.description}\n{value}"
                data.append((name, value))

        pages = MenuButtons(
            ctx=self.context,
            source=HelpPageSource(self, data),
            disable_buttons_after=True
        )
        await pages.start(self.context)

    async def send_cog_help(self, cog_):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog_), color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')

        filtered = await self.filter_commands(cog_.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=command.name,
                            value=f"```{command.short_doc}```" or 'No description Provided', inline=False)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=command.name,
                                value=f"```{command.short_doc}```" or 'No description Provided', inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.name, color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')
        if command.help:
            embed.add_field(name="Description", value=f"```{command.help}```", inline=False)
        if command.aliases:
            embed.add_field(name="Aliases", value=f"```{command.aliases}```", inline=False)
        embed.add_field(name="Usage", value=f"```{self.get_command_signature(command)}```", inline=False)
        await self.get_destination().send(embed=embed)


cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["custom_prefix"]["prefix"]

bcursor = cluster['bot']['blacklist']


async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("d!")(bot, message)
    else:
        result = await cursor.find_one({"guild": message.guild.id})
        if result is not None:
            return commands.when_mentioned_or(str(result["prefix"]))(bot, message)
        else:
            return commands.when_mentioned_or("d!")(bot, message)


intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=CustomHelp(),
                   description="One bot Many functionality", owner_id=860876181036335104, enable_debug_events=True,
                   case_insensitive=True, activity=discord.Streaming(name="d!help", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))


@bot.event
async def on_ready():
    print("""
  _____  
 |  __ \ 
 | |  | |
 | |  | |
 | |__| |
 |_____/ 
    """)
    print("""
  _____  _    _ 
 |  __ \| |  | |
 | |  | | |__| |
 | |  | |  __  |
 | |__| | |  | |
 |_____/|_|  |_|
        """)
    print("""
  _____  _    _ ____  
 |  __ \| |  | |  _ \ 
 | |  | | |__| | |_) |
 | |  | |  __  |  _ < 
 | |__| | |  | | |_) |
 |_____/|_|  |_|____/ 
            """)


@bot.check
async def block_blacklist_user(ctx):
    return await bcursor.find_one({"id": ctx.author.id}) is None

bot.add_check(block_blacklist_user)


@bot.event
async def on_command_error(ctx, error):
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


@bot.event
async def on_guild_join(guild):
    check = await cursor.find_one({"id": guild.owner.id})
    if check is not None:
        await guild.system_channel.send("Leave this server because the owner is blacklisted")
        await guild.leave()
    else:
        embed = discord.Embed(title=f"Greetings {guild.name}",
                              description="Thanks for adding DHB into your server! To get started type d!help!",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Note", value="I'm still WIP, so some features may be bugged or ugly.", inline=False)
        embed.add_field(name="Links",
                        value="[invite](https://discord.com/oauth2/authorize?client_id=875589545532485682&permissions=8&scope=bot%20applications.commands) \n[Support Server](https://discord.gg/cnydBRnHU9)",
                        inline=False)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/875589545532485682/6fd951c10178ec9bc5cb145fec56c89f.png?size=1024")
        await guild.system_channel.send(embed=embed)

cog_list = ['audio', 'economy', 'entertainment', 'leveling', 'moderation', 'owner', 'rtfm', 'settings', 'tag', 'utilities']

if __name__ == '__main__':
    # Load extension
    for folder in cog_list:
        bot.load_extension(f'cogs.{folder}')
    bot.load_extension('jishaku')

    bot.run(config_var['token'])
