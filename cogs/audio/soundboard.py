import discord
from discord import FFmpegPCMAudio
import asyncio
from discord.ext import commands

NOT_CONNECTED_TO_VOICE = "You're not connected to a vc"


class SoundBoard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Ruin your boss meeting with this")
    async def airhorn(self, ctx):
        if not ctx.author.voice:
            await ctx.send(NOT_CONNECTED_TO_VOICE)
        else:
            await ctx.message.add_reaction("🔊")
            vc = await ctx.author.voice.channel.connect()
            vc.play(FFmpegPCMAudio(source="./sounds/mlg-airhorn.mp3"))
            while vc.is_playing():
                await asyncio.sleep(5)
            await vc.disconnect()


def setup(bot):
    bot.add_cog(SoundBoard(bot))
