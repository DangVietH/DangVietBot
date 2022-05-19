import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
from utils import DefaultPageSource, MenuPages


class Leveling(commands.Cog):
    emoji = "📊"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="See your exp")
    async def rank(self, ctx, user: discord.Member = None):
        if await self.bot.mongo["levelling"]['disable'].find_one({"guild": ctx.guild.id}):
            return await ctx.send("Level system is disabled in this server")
        user = user or ctx.author
        stats = await self.bot.mongo["levelling"]['member'].find_one({'guild': ctx.guild.id, "user": user.id})
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
        ranking = self.bot.mongo["levelling"]['member'].find({'guild': ctx.guild.id}).sort("xp", -1)
        async for x in ranking:
            rank += 1
            if stats['user'] == x['user']:
                break

        IMAGE_WIDTH = 900
        IMAGE_HEIGHT = 250

        img_link = "https://cdn.discordapp.com/attachments/875886792035946496/953533593207062588/2159517.jpeg"
        CustomImg = await self.bot.mongo["levelling"]['image'].find_one({"guild": ctx.guild.id, "member": user.id})
        if CustomImg is not None:
            img_link = CustomImg["image"]

        resp = await self.bot.session.get(img_link)
        image = Image.open(io.BytesIO(await resp.read())).convert("RGBA")

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
        if await self.bot.mongo["levelling"]['disable'].find_one({"guild": ctx.guild.id}):
            return await ctx.send("Level system is disabled in this server")
        stats = self.bot.mongo["levelling"]['member'].find({'guild': ctx.guild.id}).sort("xp", -1)
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
        stats = self.bot.mongo["levelling"]['member'].find().sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {self.bot.get_user(x['user'])}",
                         f"**Server:** {self.bot.get_guild(x['guild'])} **Level:** {x['level']} **XP:** {x['xp']}")
            data.append(to_append)

        pages = MenuPages(DefaultPageSource(f"Global Leaderboard", data), ctx)
        await pages.start()

    @commands.command(help="Set background for your server rank")
    async def setbackground(self, ctx, *, link):
        if await self.bot.mongo["levelling"]['image'].find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is not None:
            await self.bot.mongo["levelling"]['image'].update_one({"guild": ctx.guild.id, "member": ctx.author.id}, {"$set": {"image": link}})
        else:
            await self.bot.mongo["levelling"]['image'].insert_one({"guild": ctx.guild.id, "member": ctx.author.id, "image": link})
        await ctx.send("New Background set")

    @commands.command(help="Set background back to default")
    async def resetbackground(self, ctx):
        if await self.bot.mongo["levelling"]['image'].find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is None:
            await ctx.send("You don't have a custom background")
        await self.bot.mongo["levelling"]['image'].delete_one({"guild": ctx.guild.id, "member": ctx.author.id})
        await ctx.send("👍")

    @commands.command(help="Add xp to member")
    @commands.has_permissions(manage_channels=True)
    async def add_xp(self, ctx, member: discord.Member, amount: int):
        if await self.bot.mongo["levelling"]['member'].find_one({'guild': ctx.guild.id, "user": ctx.author.id}) is None:
            return await ctx.send("User has no account")
        await self.bot.mongo["levelling"]['member'].update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": amount}})
        await ctx.send(f"Successfully added {amount} xp to {member}")

    @commands.command(help="Remove xp from member")
    @commands.has_permissions(manage_channels=True)
    async def remove_xp(self, ctx, member: discord.Member, amount: int):
        if await self.bot.mongo["levelling"]['member'].find_one({'guild': ctx.guild.id, "user": ctx.author.id}) is None:
            return await ctx.send("User has no account")

        await self.bot.mongo["levelling"]['member'].update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": -amount}})
        await ctx.send(f"Successfully remove {amount} xp from {member}")

    @commands.has_permissions(manage_messages=True)
    @commands.command(help="Set xp for each msg")
    async def setXpPermessage(self, ctx, level: int):
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id}, {"$set": {"xp": level}})
        await ctx.send(f"Xp per message set to {level}")

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                if await self.bot.mongo["levelling"]['member'].find_one({"guild": guild.id, "user": member.id}):
                    await self.bot.mongo["levelling"]['member'].delete_one({"guild": guild.id, "user": member.id})
                if await self.bot.mongo["levelling"]['image'].find_one({"guild": guild.id, "user": member.id}):
                    await self.bot.mongo["levelling"]['image'].delete_one({"guild": guild.id, "user": member.id})
        await self.bot.mongo["levelling"]['roles'].delete_one({"guild": guild.id})
        if await self.bot.mongo["levelling"]['disable'].find_one({"guild": guild.id}):
            await self.bot.mongo["levelling"]['disable'].delete_one({"guild": guild.id})
        if await self.bot.mongo["levelling"]['channel'].find_one({"guild": guild.id}):
            await self.bot.mongo["levelling"]['roles'].delete_one({"guild": guild.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await self.bot.mongo["levelling"]['member'].find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await self.bot.mongo["levelling"]['member'].delete_one({"guild": member.guild.id, "user": member.id})
            if await self.bot.mongo["levelling"]['image'].find_one({"guild": member.guild.id, "member": member.id}):
                await self.bot.mongo["levelling"]['image'].delete_one({"guild": member.guild.id, "member": member.id})
