from .info import Info
from .misc import Misc


def setup(bot):
    bot.add_cog(Info(bot))
    bot.add_cog(Misc(bot))