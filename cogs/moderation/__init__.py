from .admin import Admin
from .giveaway import Giveaway


def setup(bot):
    bot.add_cog(Admin(bot))
    bot.add_cog(Giveaway(bot))