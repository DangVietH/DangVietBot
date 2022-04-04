from .info import Info
from .giveaway import Giveaway


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
    await bot.add_cog(Info(bot))