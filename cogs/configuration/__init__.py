from .config import Configuration
from .customslash import CustomSlash


async def setup(bot):
    await bot.add_cog(Configuration(bot))