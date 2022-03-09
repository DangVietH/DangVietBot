from .economy import Economy
from .business import Business


def setup(bot):
    bot.add_cog(Economy(bot))