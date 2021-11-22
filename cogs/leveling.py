import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
from easy_pil import Editor, Canvas, load_image_async, Font, Text

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
            user_data = {
                "name": f"{member}",
                "xp": f"{stats['xp']}",
                "next_level_xp": f"{(int(stats['level']) + 1) * 100}",
                "level": f"{stats['level']}",
            }

            next_level_xp = (stats["level"] + 1) * 100
            current_level_xp = stats["level"] * 100
            xp_need = next_level_xp - current_level_xp
            xp_have = stats["xp"] - current_level_xp

            poppins = Font().poppins(size=40)

            percentage = (xp_need / 100) * xp_have

            avt = await load_image_async(str(member.avatar.url))

            profile = Editor(avt).resize((190, 190)).circle_image()
            background = Editor(Canvas((934, 282), "#23272a"))
            background.rectangle((20, 20), 894, 242, "#2a2e35")
            background.paste(profile, (50, 50))
            background.ellipse((42, 42), width=206, height=206, outline="#43b581", stroke_width=10)
            background.rectangle((260, 180), width=630, height=40, fill="#484b4e", radius=20)

            rank = 0
            rankings = await member.find({"guild": ctx.guild.id}).sort("xp", -1)
            for x in rankings:
                rank += 1
                if stats["user"] == x["user"]:
                    break

            background.bar(
                (260, 180),
                max_width=630,
                height=40,
                percentage=percentage,
                fill="#00fa81",
                radius=20,
            )
            background.text(
                (870, 125),
                f"{user_data['xp']} / {user_data['next_level_xp']}",
                font=poppins,
                color="#00fa81",
                align="right",
            )
            rank_level_texts = [
                Text("Rank ", color="#00fa81", font=poppins),
                Text(f"{rank}", color="#1EAAFF", font=poppins),
                Text("   Level ", color="#00fa81", font=poppins),
                Text(f"{user_data['level']}", color="#1EAAFF", font=poppins),
            ]
            background.multicolor_text((850, 30), texts=rank_level_texts, align="right")
            file = discord.File(fp=background.image_bytes, filename="rank.png")
            await ctx.send(file=file)
        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")


def setup(bot):
    bot.add_cog(Leveling(bot))
