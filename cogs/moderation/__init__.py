from .admin import Admin
from .giveaway import Giveaway
from .modset import ModSet


async def setup(bot):
    await bot.add_cog(Admin(bot))
    await bot.add_cog(ModSet(bot))
    await bot.add_cog(Giveaway(bot))