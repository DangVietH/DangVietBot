from .prefix import Prefix
from .reaction import Reaction
from .welcome import Welcome
from .setup import Setup
from .sb import Star


async def setup(bot):
    await bot.add_cog(Prefix(bot))
    await bot.add_cog(Star(bot))
    await bot.add_cog(Reaction(bot))
    await bot.add_cog(Welcome(bot))
    await bot.add_cog(Setup(bot))