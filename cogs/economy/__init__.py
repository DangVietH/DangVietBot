from .economy import Economy
from .business import Business


async def setup(bot):
    await bot.add_cog(Economy(bot))