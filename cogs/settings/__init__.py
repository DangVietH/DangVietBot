from .prefix import Prefix
from .reaction import Reaction
from .welcome import Welcome
from .setup import Setup
from .gc import GlobalChat


def setup(bot):
    bot.add_cog(Prefix(bot))
    bot.add_cog(Reaction(bot))
    bot.add_cog(Welcome(bot))
    bot.add_cog(Setup(bot))
    bot.add_cog(GlobalChat(bot))