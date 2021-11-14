from discord.ext import commands
import discordSuperUtils
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
        self.ImageManager = discordSuperUtils.ImageManager()
        super().__init__()

    @commands.command(help="Setup welcome message channel")
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

    @commands.command(help="Setup welcome message text")
    @commands.has_permissions(administrator=True)
    async def welcome_text(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't set a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
            await ctx.send(f"Welcome message updated to ```{text}```")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        result = await cursors.find_one({"guild": member.guild.id})
        if result is None:
            return
        else:
            channel = self.client.get_channel(result["channel"])
            member_count = member.guild.member_count
            await channel.send(
                str(result["message"]).format(mention=member.mention, count=member_count, name=member.name, guild=member.guild.name, username=member),
                file=await self.ImageManager.create_welcome_card(
                    member,
                    discordSuperUtils.Backgrounds.FOREST,
                    f"🎉 {member} just joined the server",
                    f"Member {member_count}",
                    description_color=(255, 255, 255),
                    transparency=127,
                )
            )
            if not member.client:
                await member.send(result["dm"])


def setup(client):
    client.add_cog(Welcome(client))
