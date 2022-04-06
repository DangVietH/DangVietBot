from .fun import Fun
from .games import Games
from .giveaway import Giveaway


async def setup(bot):
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Games(bot))
    await bot.add_cog(Giveaway(bot))