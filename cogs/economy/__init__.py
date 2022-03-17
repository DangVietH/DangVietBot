from .economy import Economy


def setup(bot):
    bot.add_cog(Economy(bot))