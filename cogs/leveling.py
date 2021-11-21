import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]
member = db['member']
role = db['roles']


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            if not message.author.bot:
                result = await member.find_one({'guild': message.guild.id, "user": message.author.id})
                if result is None:
                    insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 0}
                    await member.insert_one(insert)
                else:
                    add_exp = result['xp'] + 5
                    await member.update_one({"guild": message.guild.id, "user": message.author.id}, {"$set": {"xp": add_exp}})
                    lvl_start = result['level']
                    lvl_end = int(result['xp'] ** (1 / 4))
                    if lvl_start < lvl_end:
                        new_lvl = lvl_start + 1
                        await member.update_one({"guild": message.guild.id, "user": message.author.id}, {"$set": {"level": new_lvl}})
                        await message.channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")

    @commands.command(help="See your rank")
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        result = await member.find_one({'guild': ctx.guild.id, "user": user.id})
        if result is not None:
            embed = discord.Embed(title=user, color=user.color)
            embed.add_field(name="Level", value=f"#{result['level']}")
            embed.add_field(name="XP", value=f"#{result['xp']}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The specified member haven't send a message yet!!")


def setup(bot):
    bot.add_cog(Leveling(bot))
