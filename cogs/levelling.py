import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]


class Leveling(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.role = db['roles']
        self.xp = db['xp']

    async def update_user(self, user):
        result = await self.xp.find_one({"guild": user.guild.id})
        if user.guild.id != result['guild'] and user.id != ['member']:
            insert = {"guild": user.guild.id, "member": user.id, "rank": 0, "xp": 0}
            await self.xp.insert_one(insert)

    async def add_exp(self, user):
        result = await self.xp.find_one({"guild": user.guild.id})
        add_xp = result["xp"] + 5
        await self.xp.update_one({"guild": user.guild.id}, {"$set": {"xp": add_xp}})

    async def level_up(self, user, message):
        result = await self.xp.find_one({"guild": user.guild.id})
        lvl_og = result['rank']
        lvl_end = int(result['xp'] ** (1/4))
        if lvl_og < lvl_end:
            new_lvl = lvl_og + 1
            await self.xp.update_one({"guild": user.guild.id}, {"$set": {"rank": new_lvl}})
            await message.channel.send(f"🎉 {user.mention} has reach level **{new_lvl}**!!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            if not message.author.bot:
                await self.update_user(message.author)
                await self.add_exp(message.author)
                await self.level_up(message.author, message)

    @commands.command(help="See your rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        result = await self.xp.find_one({"guild": member.guild.id})
        if result is None:
            await ctx.send(f"The specified member haven't send a message yet!")
        else:
            embed = discord.Embed(title=member, color=member.color)
            embed.add_field(name="Level", value=f"#{result['rank']}")
            embed.add_field(name="XP", value=f"#{result['xp']}")
            await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Leveling(client))
