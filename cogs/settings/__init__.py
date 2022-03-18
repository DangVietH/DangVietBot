from .prefix import Prefix
from .reaction import Reaction
from .welcome import Welcome
from .setup import Setup
from .gc import GlobalChat


async def setup(bot):
    await bot.add_cog(Prefix(bot))
    await bot.add_cog(Reaction(bot))
    await bot.add_cog(Welcome(bot))
    await bot.add_cog(Setup(bot))
    await bot.add_cog(GlobalChat(bot))