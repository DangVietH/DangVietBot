import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
from easy_pil import Editor, Canvas, load_image_async, Font

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
            next_level_xp = (stats["level"] + 1) * 100
            current_level_xp = stats["level"] * 100
            xp_need = next_level_xp - current_level_xp
            xp_have = stats["xp"] - current_level_xp

            percentage = (xp_need / 100) * xp_have

            background = Editor(Canvas((934, 282), "#23272a"))
            profile = await load_image_async(str(member.avatar.url))

            profile = Editor(profile).resize((150, 150)).circle_image()

            poppins = Font().poppins(size=40)
            poppins_small = Font().poppins(size=30)

            square = Canvas((500, 500), "#06FFBF")
            square = Editor(square)
            square.rotate(30, expand=True)

            background.paste(square.image, (600, -250))
            background.paste(profile.image, (30, 30))

            background.rectangle((30, 220), width=650, height=40, fill="white", radius=20)
            background.bar(
                (30, 220),
                max_width=650,
                height=40,
                percentage=percentage,
                fill="#FF56B2",
                radius=20,
            )
            background.text((200, 40), str(member), font=poppins, color="white")

            background.rectangle((200, 100), width=350, height=2, fill="#17F3F6")
            background.text(
                (200, 130),
                f"Level : {stats['level']}"
                + f" XP : {stats['xp']} / {(stats['level'] + 1) * 100}",
                font=poppins_small,
                color="white",
            )

            file = discord.File(fp=background.image_bytes, filename="rank.png")
            await ctx.send(file=file)

        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")


def setup(bot):
    bot.add_cog(Leveling(bot))
