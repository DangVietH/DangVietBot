import os
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient


class CustomHelp(commands.HelpCommand):

    def get_ending_note(self):
        return f'Use help [command] for more info on a command. \nYou can also type help [category] for more info on a category'

    def get_command_signature(self, command):
        return f'{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='DHB Commands',
                              description=f"{self.context.bot.description}",
                              color=discord.Color.from_rgb(225, 0, 92))

        for cog, command in mapping.items():
            command_signatures = [self.get_command_signature(c) for c in command]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)
        embed.set_footer(text=self.get_ending_note())
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Invite', url='https://bit.ly/3daeOIe'))
        view.add_item(discord.ui.Button(label='My server', url='https://discord.gg/cnydBRnHU9'))
        view.add_item(discord.ui.Button(label='Github', url='https://github.com/DangVietH/DHB'))
        await self.get_destination().send(embed=embed, view=view)

    async def send_cog_help(self, cog_):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog_), color=discord.Color.from_rgb(225, 0, 92))
        if cog_.description:
            embed.description = cog_.description

        filtered = await self.filter_commands(cog_.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=command.name,
                            value=f"```{command.short_doc}```" or 'No description Provided', inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, color=discord.Color.from_rgb(225, 0, 92))
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=command.name,
                                value=f"```{command.short_doc}```" or 'No description Provided', inline=False)

        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.name, color=discord.Color.from_rgb(225, 0, 92))
        if command.help:
            embed.add_field(name="Description", value=f"```{command.help}```", inline=False)
        if command.aliases:
            embed.add_field(name="Aliases", value=f"```{command.aliases}```", inline=False)
        embed.add_field(name="Usage", value=f"```{self.get_command_signature(command)}```", inline=False)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)


cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
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
                   case_insensitive=True, activity=discord.Streaming(name="Happy new Year!", url="https://www.twitch.tv/dvieth"))


@bot.event
async def on_ready():
    print('DHB is online')


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
        await ctx.send("Only ! DvH#9980 (the creator) can use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You are missing a required argument for this command to work")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'⏱️ This command is on a cooldown. Use it after {round(error.retry_after, 2)}s')
    else:
        await ctx.send(error)


@bot.event
async def on_connect():
    await bot.process_commands()


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
                        value="[invite](https://discord.com/oauth2/authorize?client_id=875589545532485682&permissions=8&scope=bot%20applications.commands) \n[Support Server](https://discord.gg/cnydBRnHU9) \n[Github](https://github.com/DangVietH/DHB)",
                        inline=False)
        await guild.system_channel.send(embed=embed)

cog_list = ['audio', 'economy', 'entertainment', 'leveling', 'moderation', 'owner', 'rtfm', 'settings', 'tag', 'utilities']

if __name__ == '__main__':
    # Load extension
    for folder in cog_list:
        bot.load_extension(f'cogs.{folder}')
    bot.load_extension('jishaku')

    bot.run(os.environ.get("token"))
