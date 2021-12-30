from .admin import Admin
from .giveaway import Giveaway
from .automod import AutoMod


def setup(bot):
    bot.add_cog(Admin(bot))
    bot.add_cog(Giveaway(bot))
    bot.add_cog(AutoMod(bot))