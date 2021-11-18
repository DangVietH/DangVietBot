from discord.ext import commands
import discordSuperUtils


class Listener(commands.Cog):
    """
    Commands to listen to events
    """
    def __init__(self, client):
        self.client = client
        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        member = message.author

        if message.content.startswith("D!"):
            await message.channel.send("My commands prefix is case sensitive, so please use d! instead")
        if message.content.startswith("f "):
            await message.channel.send("f")

        # prevent
        racist = ["nigger", "nigga", "chink"]

        if any(word in message.content.lower() for word in racist):
            member.kick(reason=None)
            await message.channel.send(f"{member.mention} has been kick for saying a racist word")


def setup(client):
    client.add_cog(Listener(client))
