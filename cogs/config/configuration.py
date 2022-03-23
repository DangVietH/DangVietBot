from cogs.config.sb import Star
from cogs.config.prefix import Prefix
from cogs.config.reaction import Reaction
from cogs.config.welcome import Welcome
from discord.ext import commands


class ConfigurationBase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


class Configuration(Prefix, Reaction, Star, Welcome):
    """ Configuration commands """
    emoji = "🛠"
