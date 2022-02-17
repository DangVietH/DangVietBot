from .admin import Admin
from .giveaway import Giveaway
from .modset import ModSet


def setup(bot):
    bot.add_cog(Admin(bot))
    bot.add_cog(Giveaway(bot))
    bot.add_cog(ModSet(bot))