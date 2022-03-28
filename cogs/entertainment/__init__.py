from .fun import Fun
from .games import Games


async def setup(bot):
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Games(bot))