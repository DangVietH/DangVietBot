from .log import ModLog
from .mod import ModEvent


async def setup(bot):
    await bot.add_cog(ModLog(bot))
    await bot.add_cog(ModEvent(bot))