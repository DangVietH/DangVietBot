from .admin import Admin
from .giveaway import Giveaway
from .modutils import ModUtils


def setup(bot):
    bot.add_cog(Admin(bot))
    bot.add_cog(ModUtils(bot))
    bot.add_cog(Giveaway(bot))