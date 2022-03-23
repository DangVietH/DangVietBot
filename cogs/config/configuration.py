from discord.ext import commands


class ConfigurationBase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
