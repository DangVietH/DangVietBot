from .sb import Star
from .prefix import Prefix
from .reaction import Reaction
from .welcome import Welcome


class Configuration(Prefix, Reaction, Star, Welcome):
    """ Configuration commands """
    emoji = "🛠"


async def setup(bot):
    await bot.add_cog(Configuration(bot))