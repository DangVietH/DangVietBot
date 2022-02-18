import nextcord as discord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var
from PIL import Image, ImageDraw, ImageFont

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursors = cluster["welcome"]["channel"]


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        result = await cursors.find_one({"guild": member.guild.id})
        if result is None:
            return
        else:
            channel = self.bot.get_channel(result["channel"])
            member_count = member.guild.member_count
            embed = discord.Embed(title=f"Welcome to {member.guild.name}!",
                                  description=str(result["message"]).format(mention=member.mention, count=member_count,
                                                                            name=member.name, guild=member.guild.name,
                                                                            username=member),
                                  color=discord.Color.random())
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_image(url="https://c.tenor.com/XUgZ2mGI-LwAAAAC/welcome-greet.gif")
            await channel.send(embed=embed)
            if not member.bot:
                await member.send(
                    str(result["dm"]).format(count=member_count, name=member.name, guild=member.guild.name,
                                             username=member))

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursors.find_one({"guild": guild.id})
        if result is not None:
            await cursors.delete_one({"guild": guild.id})
