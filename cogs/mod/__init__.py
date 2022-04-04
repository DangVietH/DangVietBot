from .moderation import Moderation
from .modutils import ModUtils


async def setup(bot):
    await bot.add_cog(Moderation(bot))
    await bot.add_cog(ModUtils(bot))