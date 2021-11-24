import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]
levelling = db['member']
role = db['roles']


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            if not message.author.bot:
                stats = await levelling.find_one({'guild': message.guild.id, "user": message.author.id})
                if stats is None:
                    insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 0}
                    await levelling.insert_one(insert)
                else:
                    add_exp = stats['xp'] + 5
                    await levelling.update_one({"guild": message.guild.id, "user": message.author.id}, {"$set": {"xp": add_exp}})
                    lvl_start = stats['level']
                    lvl_end = int(stats['xp'] ** (1 / 4))
                    if lvl_start < lvl_end:
                        new_lvl = lvl_start + 1
                        await levelling.update_one({"guild": message.guild.id, "user": message.author.id}, {"$set": {"level": new_lvl}})
                        await message.channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")

    @commands.command(help="See your rank")
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        stats = await levelling.find_one({'guild': ctx.guild.id, "user": user.id})
        if stats is not None:
            embed = discord.Embed(title=user, color=user.color)
            embed.add_field(name="Level", value=f"#{stats['level']}")
            embed.add_field(name="XP", value=f"#{stats['xp']}")
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")

    @commands.command(help="See the top 20 users in your server")
    async def top(self, ctx):
        stats = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
        i = 1
        embed = discord.Embed(title=f"🏆 Leaderboard of {ctx.guild.id}", color=discord.Color.random())
        stat_list = await stats.to_list()
        for x in stats:
            try:
                temp = ctx.guild.get_member(x["user"])
                tempxp = x["xp"]
                templvl = x["level"]
                xp = "{:,}".format(tempxp)
                level = "{:,}".format(templvl)
                embed.add_field(name=f"{i}: {temp}", value=f"**Level:** {level}  **XP:** {xp}", inline=True)
                i += 1            
            except:
                pass
            if i == 20 + 1:
                break
        await ctx.send(embed=embed)
    
    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                await levelling.delete_one({"guild": guild.id, "user": member.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            await levelling.delete_one({"guild": member.guild.id, "user": member.id})


def setup(bot):
    bot.add_cog(Leveling(bot))
