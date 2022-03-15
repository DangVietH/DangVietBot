from .music import Music
from .socketfix import SocketFix


def setup(bot):
    bot.add_cog(Music(bot))
    bot.add_cog(SocketFix(bot))