import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont
import io
from utils import get_image_from_url, DefaultPageSource, MenuPages, config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["levelling"]
levelling = db['member']
disable = db['disable']
lvlConfig = db['roles']
upchannel = db['channel']
image_cursor = db['image']


class Leveling(commands.Cog):
    emoji = "📊"

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if await disable.find_one({"guild": message.guild.id}):
            return
        stats = await levelling.find_one({'guild': message.guild.id, "user": message.author.id})
        if stats is None:
            insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 5}
            await levelling.insert_one(insert)
        else:
            lconf = await lvlConfig.find_one({"guild": message.guild.id})
            await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                       {"$inc": {"xp": int(lconf['xp'])}})

            xp = stats['xp']
            lvl = 0
            while True:
                if xp < ((100 / 2 * (lvl ** 2)) + (100 / 2 * lvl)):
                    break
                lvl += 1

            xp -= ((100 / 2 * ((lvl - 1) ** 2)) + (100 / 2 * (lvl - 1)))
            if stats["xp"] < 0:
                levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                     {"$set": {"xp": 0}})
            if stats['level'] < lvl:
                await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                           {"$inc": {"level": 1}})

                lvl_channel = await upchannel.find_one({"guild": message.guild.id})
                if lvl_channel is None:
                    return await message.channel.send(lconf['msg'].format(
                        mention=message.author.mention,
                        name=message.author.name,
                        server=message.guild.name,
                        username=message.author,
                        level=stats['level'] + 1
                    ))

                channel = self.bot.get_channel(lvl_channel["channel"])
                await channel.send(lconf['msg'].format(
                    mention=message.author.mention,
                    name=message.author.name,
                    server=message.guild.name,
                    username=message.author,
                    level=stats['level'] + 1
                ))

                levelrole = lconf['role']
                levelnum = lconf['level']
                for i in range(len(levelrole)):
                    if lvl == int(levelnum[i]):
                        role = message.guild.get_role(int(levelrole[i]))
                        await message.author.add_roles(role)
                        lvl_channel = await upchannel.find_one({"guild": message.guild.id})
                        if lvl_channel is None:
                            return await message.channel.send(
                                f"{message.author}also receive {role.name} role")
                        channel = self.bot.get_channel(lvl_channel["channel"])
                        await channel.send(f"🎉 {message.author} also receive {role.name} role")

    @commands.command(help="See your exp")
    async def rank(self, ctx, user: discord.Member = None):
        if await disable.find_one({"guild": ctx.guild.id}):
            return await ctx.send("Level system is disabled in this server")
        user = user or ctx.author
        stats = await levelling.find_one({'guild': ctx.guild.id, "user": user.id})
        if stats is None:
            return await ctx.send("The specified member haven't send a message in this server!!")
        lvl = 0
        rank = 0
        xp = stats["xp"]
        while True:
            if xp < ((100 / 2 * (lvl ** 2)) + (100 / 2 * lvl)):
                break
            lvl += 1
        xp -= ((100 / 2 * (lvl - 1) ** 2) + (100 / 2 * (lvl - 1)))
        ranking = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
        async for x in ranking:
            rank += 1
            if stats['user'] == x['user']:
                break

        IMAGE_WIDTH = 900
        IMAGE_HEIGHT = 250

        img_link = "https://cdn.discordapp.com/attachments/875886792035946496/953533593207062588/2159517.jpeg"
        CustomImg = await image_cursor.find_one({"guild": ctx.guild.id, "member": user.id})
        if CustomImg is not None:
            img_link = CustomImg["image"]
        image = Image.open(get_image_from_url(
            img_link)).convert("RGBA")

        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT))

        rectangle_image = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT))
        rectangle_draw = ImageDraw.Draw(rectangle_image)
        rectangle_draw.rectangle((20, 20, IMAGE_WIDTH - 20, IMAGE_HEIGHT - 20), fill=(0, 0, 0, 127))
        image = Image.alpha_composite(image, rectangle_image)

        draw = ImageDraw.Draw(image)

        font_big = ImageFont.truetype('font.ttf', 36)
        font_small = ImageFont.truetype('font.ttf', 20)

        needed_xp = 100 * 2 * ((1 / 2) * lvl)
        draw.text((248, 48), f"{user}", fill=(225, 0, 92), font=font_big)
        draw.text((641, 48), f"Rank #{rank}", fill=(225, 0, 92), font=font_big)
        draw.text((248, 130), f"Level {stats['level']}", fill=(225, 0, 92), font=font_small)
        draw.text((641, 130), f"{xp} / {needed_xp} XP", fill=(225, 0, 92), font=font_small)

        draw.rounded_rectangle((242, 182, 803, 208), fill=(70, 70, 70), outline=(225, 0, 92), radius=13, width=3)

        bar_length = 245 + xp / needed_xp * 205
        draw.rounded_rectangle((245, 185, bar_length, 205), fill=(225, 0, 92), radius=10)

        AVATAR_SIZE = 200
        avatar_asset = user.display_avatar.replace(format='jpg', size=128)
        buffer_avatar = io.BytesIO(await avatar_asset.read())

        buffer_avatar = io.BytesIO()
        await avatar_asset.save(buffer_avatar)
        buffer_avatar.seek(0)

        # read JPG from buffer to Image
        avatar_image = Image.open(buffer_avatar)
        avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE))

        circle_image = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
        circle_draw = ImageDraw.Draw(circle_image)
        circle_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

        x = 40
        y = (IMAGE_HEIGHT - AVATAR_SIZE) // 2
        image.paste(avatar_image, (x, y), circle_image)

        buffer = io.BytesIO()

        # save PNG in buffer
        image.save(buffer, format='PNG')

        # move to beginning of buffer so `send()` it will read from beginning
        buffer.seek(0)

        await ctx.send(file=discord.File(buffer, 'rank.png'))

    @commands.command(help="See server ranks")
    async def top(self, ctx):
        if await disable.find_one({"guild": ctx.guild.id}):
            return await ctx.send("Level system is disabled in this server")
        stats = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {ctx.guild.get_member(x['user'])}", f"**Level:** {x['level']} **XP:** {x['xp']}")
            data.append(to_append)

        page = MenuPages(DefaultPageSource(f"Leaderboard of {ctx.guild.name}", data), ctx)
        await page.start()

    @commands.command(help="See global rank")
    @commands.is_owner()
    async def gtop(self, ctx):
        stats = levelling.find().sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {self.bot.get_user(x['user'])}",
                         f"**Server:** {self.bot.get_guild(x['guild'])} **Level:** {x['level']} **XP:** {x['xp']}")
            data.append(to_append)

        pages = MenuPages(DefaultPageSource(f"Global Leaderboard", data), ctx)
        await pages.start()

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                result = await levelling.find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await levelling.delete_one({"guild": guild.id, "user": member.id})
        await lvlConfig.delete_one({"guild": guild.id})
        if await disable.find_one({"guild": guild.id}) is not None:
            await disable.delete_one({"guild": guild.id})
        if await upchannel.find_one({"guild": guild.id}) is not None:
            await lvlConfig.delete_one({"guild": guild.id})
        if await image_cursor.find_one({"guild": guild.id}) is True:
            await image_cursor.delete_one({"guild": guild.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await levelling.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await levelling.delete_one({"guild": member.guild.id, "user": member.id})
            if await image_cursor.find_one({"guild": member.guild.id, "member": member.id}) is True:
                await image_cursor.delete_one({"guild": member.guild.id, "member": member.id})
