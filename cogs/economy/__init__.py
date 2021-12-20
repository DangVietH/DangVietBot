from .economy import Economy
from .server_economy import ServerEconomy


def setup(bot):
    bot.add_cog(Economy(bot))
    bot.add_cog(ServerEconomy(bot))