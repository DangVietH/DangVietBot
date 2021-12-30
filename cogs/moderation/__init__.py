from .admin import Admin
from .giveaway import Giveaway
from .automod import AutoMod
from automod_event import AutoModEvent


def setup(bot):
    bot.add_cog(Admin(bot))
    bot.add_cog(Giveaway(bot))
    bot.add_cog(AutoMod(bot))
    bot.add_cog(AutoModEvent(bot))