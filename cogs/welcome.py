from discord.ext import commands
import discord
from motor.motor_asyncio import AsyncIOMotorClient
import json

with open('config.json') as f:
    data = json.load(f)

cluster = AsyncIOMotorClient(data['mango_link'])
dbs = cluster["welcome"]
cursors = dbs["channel"]


class Welcome(commands.Cog):
    def __init__(self, client):
        self.client = client
        super().__init__()

    @commands.command(help="Setup welcome channel")
    @commands.has_permissions(administrator=True)
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}", "dm": f"Have fun at **{ctx.guild.name}**"}
            await cursors.insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        elif result is not None:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @commands.command(help="Setup welcome text")
    @commands.has_permissions(administrator=True)
    async def welcome_text(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't set a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
            await ctx.send(f"Welcome message updated to ```{text}```")

    @commands.command(help="Setup welcome dm")
    @commands.has_permissions(administrator=True)
    async def welcome_dm(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't set a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
            await ctx.send(f"Welcome dm updated to ```{text}```")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        result = await cursors.find_one({"guild": member.guild.id})
        if result is None:
            return
        else:
            channel = self.client.get_channel(result["channel"])
            member_count = member.guild.member_count
            embed = discord.Embed(title=f"Welcome to {member.guild.name}!", description=str(result["message"]).format(mention=member.mention, count=member_count, name=member.name, guild=member.guild.name, username=member))
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_image(url="https://c.tenor.com/XUgZ2mGI-LwAAAAC/welcome-greet.gif")
            await channel.send(embed=embed)
            if not member.bot:
                await member.send(str(result["dm"]).format(count=member_count, name=member.name, guild=member.guild.name, username=member))


def setup(client):
    client.add_cog(Welcome(client))
