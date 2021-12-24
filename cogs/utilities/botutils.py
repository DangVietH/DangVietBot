import discord
from discord.ext import commands


class BotUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Suggest something to this bot")
    async def suggest(self, ctx, *, text):
        channel = self.bot.get_channel(887949939676684338)
        embed = discord.Embed(title=f"Suggestion from {ctx.author}", description=f"{text}", color=discord.Color.from_rgb(225, 0, 92))
        msg = await channel.send(embed=embed)
        await msg.add_reaction('🔼')
        await msg.add_reaction('🔽')
        await ctx.send("Message sent to the suggestion channel in our server")

    @commands.command(help="Report a bug of the bot")
    async def bug(self, ctx, *, text):
        channel = self.bot.get_channel(921375785112195102)
        embed = discord.Embed(title=f"Bug reported by {ctx.author}", description=f"{text}",
                              color=discord.Color.from_rgb(225, 0, 92))
        msg = await channel.send(embed=embed)
        await msg.add_reaction('🔼')
        await msg.add_reaction('🔽')
        await ctx.send("Message sent to the bug channel in our server")