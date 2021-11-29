from .fun import Fun
from .game import Game


def setup(bot):
    bot.add_cog(Game(bot))
    bot.add_cog(Fun(bot))