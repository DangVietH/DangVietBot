from .info import Info
from .statcord import StatcordPost


async def setup(bot):
    await bot.add_cog(Info(bot))
    await bot.add_cog(StatcordPost(bot))