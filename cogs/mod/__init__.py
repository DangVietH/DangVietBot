from .moderation import Moderation
from .giveaway import Giveaway
from .modutils import ModUtils


async def setup(bot):
    await bot.add_cog(Moderation(bot))
    await bot.add_cog(ModUtils(bot))
    await bot.add_cog(Giveaway(bot))