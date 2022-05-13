from discord.ext import commands
import discord
import datetime


class OnError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        ignore = (commands.CommandNotFound, discord.NotFound, discord.Forbidden)

        if isinstance(error, ignore):
            return

        embed = discord.Embed(color=self.bot.embed_color)

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join([f"{x.replace('_', ' ').replace('guild', 'server').title()}" for x in error.missing_permissions])
            embed.title = "Bot Missing Permissions"
            embed.description = f"I am missing the following permissions: {perms}"
            await ctx.send(embed=embed)
            return

        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join([f"{x.replace('_', ' ').replace('guild', 'server').title()}" for x in error.missing_permissions])
            embed.title = "Missing Permissions"
            embed.description = f"You are missing the following permissions: {perms}"
            await ctx.send(embed=embed)
            return

        elif isinstance(error, commands.NotOwner):
            embed.title = "What's up with ye brain?"
            embed.description = f"You're not the owner of the bot"
            await ctx.send(embed=embed)
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            embed.title = "Missing Argument"
            embed.description = f"You are missing a required argument for this command to work: {error.param.name}"
            await ctx.send(embed=embed)
            return

        elif isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            wait_until_finish = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            await ctx.send(f'⏱️ This command is on a cooldown. Use it after <t:{int(datetime.datetime.timestamp(wait_until_finish))}:R>')
            return

        elif isinstance(error, commands.DisabledCommand):
            embed.title = "Uh oh"
            embed.description = "This command is disabled"
            await ctx.send(embed=embed)
            return
        embed.title = "Error"
        embed.description = error
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(OnError(bot))