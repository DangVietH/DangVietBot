from .tag import Tags


def setup(bot):
    bot.add_cog(Tags(bot))