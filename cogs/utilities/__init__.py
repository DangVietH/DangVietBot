from .info import Info
from .misc import Misc
from .botutils import BotUtils
from .tag import Tags
from .helpcmd import HelpCmd


def setup(bot):
    bot.add_cog(Info(bot))
    bot.add_cog(Misc(bot))
    bot.add_cog(BotUtils(bot))
    bot.add_cog(Tags(bot))
    bot.add_cog(HelpCmd(bot))