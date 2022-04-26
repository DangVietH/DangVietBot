from .reaction import Reaction
from .sb import Star
from .welcome import Welcome
from .level import Level


async def setup(bot):
    await bot.add_cog(Reaction(bot))
    await bot.add_cog(Star(bot))
    await bot.add_cog(Welcome(bot))
    await bot.add_cog(Level(bot))