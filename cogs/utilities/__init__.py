from .info import Info
from .misc import Misc
from .botutils import BotUtils
from .tag import Tags


async def setup(bot):
    await bot.add_cog(Info(bot))
    await bot.add_cog(Misc(bot))
    await bot.add_cog(BotUtils(bot))
    await bot.add_cog(Tags(bot))