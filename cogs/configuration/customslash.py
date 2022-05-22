from discord import app_commands
from discord.ext import commands


class CustomSlash(commands.Cog):
    emoji = "<:slash:977584566967603210>"

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True,
                    case_insensitive=True,
                    help="Create your own custom slash commands for your server. Note this is still in testing")
    async def customslash(self, ctx):
        await ctx.send_help(ctx.command)

    @customslash.command(name="create", description="Create the command")
    @commands.is_owner()
    async def cslash_create(self, ctx):
        questions = [
            'What is the name of the command?',
            'What is the description of the command?',
            'What is the value of the command?'
        ]
        answers = []
        msg = await ctx.send("Let's make sum slash commands")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await msg.edit(content=question)
            user_msg = await self.bot.wait_for('message', check=check)
            answers.append(user_msg.content)
            await ctx.channel.purge(limit=1)

        command = app_commands.Command(name=answers[0],
                                       description=answers[1],
                                       callback=answers[2],
                                       guild_ids=[ctx.guild.id])
        self.bot.tree.add_command(command, guild=ctx.guild)
        await ctx.send(f"Command created. To complete the process, do `{ctx.clean_prefix}customslash sync` so they can appear!")

    """
    @customslash.command(name="sync", description="Sync the commands you created to your server")
    async def cslash_sync(self, ctx):
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("All the slash commands you created or remove are now synced")
    """
