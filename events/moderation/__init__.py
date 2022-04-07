from .log import ModLog


async def setup(bot):
    await bot.add_cog(ModLog(bot))