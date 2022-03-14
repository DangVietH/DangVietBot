from discord.ext import commands, ipc


class IpcRoutes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ipc.server.route()
    async def get_guild_data(self, data):
        guild = self.bot.get_guild(data.guild_id)
        if guild is None:
            return None

        return guild.id, guild.name