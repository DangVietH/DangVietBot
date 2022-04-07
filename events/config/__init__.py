from .reaction import Reaction
from .sb import Star
from .welcome import Welcome


async def setup(bot):
    await bot.add_cog(Reaction(bot))
    await bot.add_cog(Star(bot))
    await bot.add_cog(Welcome(bot))