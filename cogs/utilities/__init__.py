from .utils import Utils
from .tag import Tags


async def setup(bot):

    await bot.add_cog(Tags(bot))
    await bot.add_cog(Utils(bot))