from .info import Info
from .misc import Misc
from .botutils import BotUtils


def setup(bot):
    bot.add_cog(Info(bot))
    bot.add_cog(Misc(bot))
    bot.add_cog(BotUtils(bot))