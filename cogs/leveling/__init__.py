from .leveling import Leveling
from .levelUtils import LevelUtils


async def setup(bot):
    await bot.add_cog(Leveling(bot))
    await bot.add_cog(LevelUtils(bot))