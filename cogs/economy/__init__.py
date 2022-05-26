from .economy import Economy
from .econevent import EconEvent


async def setup(bot):
    await bot.add_cog(Economy(bot))
    await bot.add_cog(EconEvent(bot))