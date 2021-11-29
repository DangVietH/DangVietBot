from .leveling import Leveling


def setup(bot):
    bot.add_cog(Leveling(bot))