from .moderation import Moderation


async def setup(bot):
    await bot.add_cog(Moderation(bot))