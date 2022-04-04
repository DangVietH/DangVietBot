from .music import Music
from .socketfix import SocketFix


async def setup(bot):
    await bot.add_cog(Music(bot))
    await bot.add_cog(SocketFix(bot))