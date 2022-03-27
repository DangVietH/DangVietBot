from .rtfm import RTFM


async def setup(bot):
    await bot.add_cog(RTFM(bot))