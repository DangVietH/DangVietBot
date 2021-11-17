import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]
member = db['member']
role = db['roles']


class Leveling(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            if not message.author.bot:
                result = await member.find_one({'user': message.author.id})
                if result is None:
                    insert = {'user': message.author.id, 'lvl': 0, 'xp': 0}
                    await member.insert_one(insert)
                else:
                    nxp = member['xp'] + 5
                    await member.update_one({"user": message.author.id}, {"$set": {"xp": nxp}})
                    lvl_og = result['lvl']
                    lvl_end = int(result['exp'] ** (1 / 4))
                    if lvl_og < lvl_end:
                        new_lvl = lvl_og + 1
                        await member.update_one({"user": message.author.id}, {"$set": {"lvl": new_lvl}})
                        await message.channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")

    @commands.command(help="See your rank")
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        result = await member.find_one({"user": user.id})
        if result is not None:
            embed = discord.Embed(title=user, color=user.color)
            embed.add_field(name="Level", value=f"#{result['lvl']}")
            embed.add_field(name="XP", value=f"#{result['xp']}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The specified member haven't send a message yet!")


def setup(client):
    client.add_cog(Leveling(client))
