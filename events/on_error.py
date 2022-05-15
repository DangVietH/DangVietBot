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
            embed.description = f"I am missing the following permissions: {perms}!"
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join([f"{x.replace('_', ' ').replace('guild', 'server').title()}" for x in error.missing_permissions])
            embed.title = "Missing Permissions"
            embed.description = f"You are missing the following permissions: {perms}!"
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.NotOwner):
            embed.title = "Not Owner"
            embed.description = f"You're not the owner of this bot!"
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            embed.title = "Missing Argument"
            embed.description = f"You are missing a required argument for this command to work: `{error.param.name}`!"
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            wait_until_finish = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            await ctx.send(f'⏱️ This command is on a cooldown. Use it after <t:{int(datetime.datetime.timestamp(wait_until_finish))}:R>')
            return

        if isinstance(error, commands.DisabledCommand):
            embed.title = "Disabled"
            embed.description = "This command is disabled by the bot's owner!"
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BadArgument):
            if isinstance(error, commands.MessageNotFound):
                embed.title = "Message Not Found"
                embed.description = "The message id/link you provided is invalid or deleted!"
                await ctx.send(embed=embed)
                return

            if isinstance(error, commands.MemberNotFound):
                embed.title = "Member Not Found"
                embed.description = "The member id/mention/name you provided is invalid or didn't exist in this server!"
                await ctx.send(embed=embed)
                return

            if isinstance(error, commands.UserNotFound):
                embed.title = "User Not Found"
                embed.description = "The user id/mention/name you provided is invalid or I cannot see that User!"
                await ctx.send(embed=embed)
                return

            if isinstance(error, commands.ChannelNotFound):
                embed.title = "Channel Not Found"
                embed.description = "The channel id/mention/name you provided is invalid or I access it!"
                await ctx.send(embed=embed)
                return

            if isinstance(error, commands.RoleNotFound):
                embed.title = "Role Not Found"
                embed.description = "The role id/mention/name you provided is invalid or I cannot see that role!"
                await ctx.send(embed=embed)
                return

            if isinstance(error, commands.EmojiNotFound):
                embed.title = "Emoji Not Found"
                embed.description = "The emoji id/name you provided is invalid or I cannot see that emoji!"
                await ctx.send(embed=embed)
                return

        embed.title = "Unexpected Error"
        embed.description = error
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(OnError(bot))