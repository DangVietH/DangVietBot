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
                stats = await member.find_one({'guild': message.guild.id, "user": message.author.id})
                if stats is None:
                    insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 0}
                    await member.insert_one(insert)
                else:
                    add_exp = stats['xp'] + 5
                    await member.update_one({"guild": message.guild.id, "user": message.author.id}, {"$set": {"xp": add_exp}})
                    lvl_start = stats['level']
                    lvl_end = int(stats['xp'] ** (1 / 4))
                    if lvl_start < lvl_end:
                        new_lvl = lvl_start + 1
                        await member.update_one({"guild": message.guild.id, "user": message.author.id}, {"$set": {"level": new_lvl}})
                        await message.channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")

    @commands.command(help="See your rank")
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        stats = await member.find_one({'guild': ctx.guild.id, "user": user.id})
        if stats is not None:
            xp = stats["xp"]
            lvl = stats["level"]
            rank = 0
            xp -= ((50 * ((lvl - 1) ** 2)) + (50 * (lvl - 1)))
            boxes = int((xp / (200 * ((1 / 2) * lvl))) * 20)  # shows boxes (for visual effect)
            rankings = member.find({"guild": ctx.guild.id}).sort("xp", -1)
            for x in rankings:  # to show what rank they are
                rank += 1
                if stats["user"] == x["user"]:
                    break
            # using this to send all the info
            embed = discord.Embed(title="{}'s level stats".format(ctx.author.name))
            embed.add_field(name="XP", value=f"{xp}/{int(200 * ((1 / 2) * lvl))}", inline=True)
            embed.add_field(name="Rank", value=f"{rank}/{ctx.guild.member_count}", inline=True)
            embed.add_field(name="Progress",
                            value=boxes * ":red_square:" + (20 - boxes) * ":black_large_square:", inline=False)
            embed.set_thumbnail(url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")


def setup(bot):
    bot.add_cog(Leveling(bot))
