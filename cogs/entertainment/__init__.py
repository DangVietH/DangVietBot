from .fun import Fun
from .games import Games
from .giveaway import Giveaway
from .image import Image


async def setup(bot):
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Games(bot))
    await bot.add_cog(Giveaway(bot))
    await bot.add_cog(Image(bot))