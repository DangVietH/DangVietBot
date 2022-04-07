from .config import Configuration


async def setup(bot):
    await bot.add_cog(Configuration(bot))