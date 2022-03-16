from .admin import Admin
from .giveaway import Giveaway
from .modutils import ModUtils


async def setup(bot):
    await bot.add_cog(Admin(bot))
    await bot.add_cog(ModUtils(bot))
    await bot.add_cog(Giveaway(bot))