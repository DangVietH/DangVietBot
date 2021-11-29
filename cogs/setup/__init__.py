from .prefix import Prefix
from .reaction import Reaction
from .welcome import Welcome


def setup(bot):
    bot.add_cog(Prefix(bot))
    bot.add_cog(Reaction(bot))
    bot.add_cog(Welcome(bot))