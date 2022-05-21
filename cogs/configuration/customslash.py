from discord import app_commands
from discord.ext import commands


class CustomSlash(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True,
                    case_insensitive=True,
                    help="Create your own custom slash commands for your server. Note this is still in testing")
    async def customslash(self, ctx):
        await ctx.send_help(ctx.command)

    @customslash.command(name="Create", description="Create the command")
    @commands.is_owner()
    async def cslash_create(self, ctx, name, description, *, value):
        command = app_commands.Command(name=name,
                                       description=description,
                                       callback=value,
                                       guild_ids=[ctx.guild.id])
        self.bot.tree.add_command(command, guild=ctx.guild)
        await ctx.send(f"Command created. To complete the process, do `{ctx.clean_prefix}customslash sync` so they can appear!")

    """
    @customslash.command(name="sync", description="Sync the commands you created to your server")
    async def cslash_sync(self, ctx):
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("All the slash commands you created or remove are now synced")
    """
