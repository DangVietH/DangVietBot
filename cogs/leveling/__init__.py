from .leveling import Leveling
from .levelUtils import LevelUtils


def setup(bot):
    bot.add_cog(Leveling(bot))
    bot.add_cog(LevelUtils(bot))