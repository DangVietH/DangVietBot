from discord.ext import commands
import discord
from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
dbs = cluster["welcome"]
cursors = dbs["channel"]


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.command(help="Setup welcome channel")
    @commands.has_permissions(administrator=True)
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}",
                      "dm": f"Have fun at **{ctx.guild.name}**"}
            await cursors.insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        elif result is not None:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @commands.command(help="Remove welcome system")
    @commands.has_permissions(administrator=True)
    async def remove_wchannel(self, ctx):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            await cursors.delete_one(result)
            await ctx.send("Welcome system has been remove")
        else:
            await ctx.send("You don't have a welcome system")

    @commands.command(help="Setup welcome text")
    @commands.has_permissions(administrator=True)
    async def welcome_text(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
            await ctx.send(f"Welcome message updated to ```{text}```")

    @commands.command(help="Setup welcome dm")
    @commands.has_permissions(administrator=True)
    async def welcome_dm(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
            await ctx.send(f"Welcome dm updated to ```{text}```")

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
        for member in guild.members:
            if not member.bot:
                await cursors.delete_one({"guild": guild.id})


def setup(bot):
    bot.add_cog(Welcome(bot))
