from .tag import Tag


def setup(bot):
    bot.add_cog(Tag(bot))