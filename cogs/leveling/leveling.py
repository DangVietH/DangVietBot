import nextcord as discord
from nextcord.ext import commands, menus
from motor.motor_asyncio import AsyncIOMotorClient
from utils.menuUtils import MenuButtons
from utils.configs import config_var
from PIL import Image, ImageDraw, ImageFont
import io
from utils.imageUtils import get_image_from_url

cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["levelling"]
levelling = db['member']
disable = db['disable']
roled = db['roles']
upchannel = db['channel']


class GuildLeaderboardPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url=menu.ctx.author.guild.icon.url,
            name=f"Leaderboard of {menu.ctx.author.guild.name}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class GlobalLeaderboardPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url="https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif",
            name="Global Leaderboard")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class RoleListPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url=menu.ctx.author.guild.icon.url,
            name=f"Level roles")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            if not message.author.bot:
                is_disabled = await disable.find_one({"guild": message.guild.id})
                if is_disabled is None:
                    stats = await levelling.find_one({'guild': message.guild.id, "user": message.author.id})
                    if stats is None:
                        insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 5}
                        await levelling.insert_one(insert)
                    else:
                        await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                                   {"$inc": {"xp": 10}})

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
                                await message.channel.send(
                                    f"🎉 {message.author.mention} has reached level **{lvl}**!!🎉")
                            else:
                                channel = self.bot.get_channel(lvl_channel["channel"])
                                await channel.send(f"🎉 {message.author.mention} has reach level **{lvl}**!!🎉")

                            role_reward = await roled.find_one({"guild": message.guild.id})
                            levelrole = role_reward['role']
                            levelnum = role_reward['level']
                            for i in range(len(levelrole)):
                                if lvl == int(levelnum[i]):
                                    role = message.guild.get_role(int(levelrole[i]))
                                    await message.author.add_roles(role)
                                    lvl_channel = await upchannel.find_one({"guild": message.guild.id})
                                    if lvl_channel is None:
                                        await message.channel.send(f"{message.author}also receive {role.name} role")
                                    else:
                                        channel = self.bot.get_channel(lvl_channel["channel"])
                                        await channel.send(f"🎉 {message.author} also receive {role.name} role")
                else:
                    return None

    @commands.command(help="See your rank but alpha")
    @commands.guild_only()
    async def test_rank(self, ctx, user: discord.Member = None):
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

        IMAGE_WIDTH = 933
        IMAGE_HEIGHT = 280

        image = Image.open(get_image_from_url(
            "https://cdn.discordapp.com/attachments/875886792035946496/945619357512372274/com_wallpaper.png")).convert(
            "RGBA"
        )

        image = image.resize((IMAGE_WIDTH, IMAGE_HEIGHT))

        rectangle_image = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT))
        rectangle_draw = ImageDraw.Draw(rectangle_image)
        rectangle_draw.rectangle((20, 20, IMAGE_WIDTH-20, IMAGE_HEIGHT-20), fill=(0, 0, 0, 127))
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
        avatar_asset = user.avatar.replace(format='jpg', size=128)
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

        x = 20
        y = (IMAGE_HEIGHT - AVATAR_SIZE) // 2
        image.paste(avatar_image, (x, y), circle_image)

        buffer = io.BytesIO()

        # save PNG in buffer
        image.save(buffer, format='PNG')

        # move to beginning of buffer so `send()` it will read from beginning
        buffer.seek(0)

        await ctx.send(file=discord.File(buffer, 'rank.png'))

    @commands.command(help="See your rank")
    @commands.guild_only()
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        stats = await levelling.find_one({'guild': ctx.guild.id, "user": user.id})
        if stats is not None:
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

            IMAGE_WIDTH = 850
            IMAGE_HEIGHT = 238

            image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), (40, 40, 50))
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
            avatar_asset = user.avatar.replace(format='jpg', size=128)
            buffer_avatar = io.BytesIO(await avatar_asset.read())

            buffer_avatar = io.BytesIO()
            await avatar_asset.save(buffer_avatar)
            buffer_avatar.seek(0)

            # read JPG from buffer to Image
            avatar_image = Image.open(buffer_avatar)

            # resize it
            avatar_image = avatar_image.resize((AVATAR_SIZE, AVATAR_SIZE))

            circle_image = Image.new('L', (AVATAR_SIZE, AVATAR_SIZE))
            circle_draw = ImageDraw.Draw(circle_image)
            circle_draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)

            x = 20
            y = (IMAGE_HEIGHT - AVATAR_SIZE) // 2
            image.paste(avatar_image, (x, y), circle_image)

            buffer = io.BytesIO()

            # save PNG in buffer
            image.save(buffer, format='PNG')

            # move to beginning of buffer so `send()` it will read from beginning
            buffer.seek(0)

            await ctx.send(file=discord.File(buffer, 'rank.png'))
        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")

    @commands.command(help="See server ranks")
    @commands.guild_only()
    async def top(self, ctx):
        stats = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {ctx.guild.get_member(x['user'])}", f"**Level:** {x['level']} **XP:** {x['xp']}")
            data.append(to_append)

        pages = MenuButtons(source=GuildLeaderboardPageSource(data), disable_buttons_after=True, ctx=ctx)
        await pages.start(ctx)

    @commands.command(help="See global rank")
    @commands.guild_only()
    async def gtop(self, ctx):
        stats = levelling.find().sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {self.bot.get_user(x['user'])}",
                         f"**Server:** {self.bot.get_guild(x['guild'])} **Level:** {x['level']} **XP:** {x['xp']}")
            data.append(to_append)

        pages = MenuButtons(source=GlobalLeaderboardPageSource(data), disable_buttons_after=True, ctx=ctx)
        await pages.start(ctx)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Level rewarding role setup")
    async def role(self, ctx):
        embed = discord.Embed(title="Level rewarding role setup", color=discord.Color.random())
        command = self.bot.get_command("role")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"role {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        embed.set_footer(text="Who needs MEE6 premium when we have this")
        await ctx.send(embed=embed)

    @role.command(help="Set up the roles")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add(self, ctx, level: int, roles: discord.Role):
        role_cursor = await roled.find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            await ctx.send("That role is already added")
        else:
            await roled.update_one({"guild": ctx.guild.id}, {"$push": {"role": roles.id, "level": level}})
            await ctx.send(f"{roles.name} role added.")

    @role.command(help="Remove the role from level")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove(self, ctx, level: int, roles: discord.Role):
        role_cursor = await roled.find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            await roled.update_one({"guild": ctx.guild.id}, {"$pull": {"role": roles.id, "level": level}})
            await ctx.send(f"{roles.name} role remove.")
        else:
            await ctx.send("I don't remember I put that role in. do role list to see")

    @role.command(help="See list of rewarding roles")
    @commands.guild_only()
    async def list(self, ctx):
        role_cursor = await roled.find_one({"guild": ctx.guild.id})
        levelrole = role_cursor['role']
        levelnum = role_cursor['level']
        embed = discord.Embed(title="Role Rewards")
        for i in range(len(levelrole)):
            embed.add_field(name=f"Level {levelnum[i]}", value=f"Role reward: {ctx.guild.get_role(levelrole[i]).name}")
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Level channel setup")
    async def lvl(self, ctx):
        embed = discord.Embed(title="Level up utils", color=discord.Color.random())
        command = self.bot.get_command("lvl")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"lvl {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @lvl.command(help="Setup level up channel if you like to")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def set(self, ctx, channel: discord.TextChannel):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await upchannel.insert_one(insert)
            await ctx.send(f"Level up channel set to {channel.mention}")
        elif result is not None:
            await upchannel.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Level up channel updated to {channel.mention}")

    @lvl.command(help="Remove level up channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove(self, ctx):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a level up channel")
        else:
            await upchannel.delete_one(result)

    @lvl.command(help="Disable levelling")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def disable(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await ctx.send("Bruh")
        else:
            insert = {"guild": ctx.guild.id}
            await disable.insert_one(insert)
            for member in ctx.guild.members:
                if not member.bot:
                    result = await levelling.find_one({"guild": ctx.guild.id, "user": member.id})
                    if result is not None:
                        await levelling.delete_one({"guild": ctx.guild.id, "user": member.id})
            await ctx.send('Levelling disabled')

    @lvl.command(help="Re-enable levelling")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def renable(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await disable.delete_one(check)
            await ctx.send('Levelling re-enable')
        else:
            await ctx.send('Leveling already enabled')

    @commands.command(help="Add xp to member")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add_xp(self, ctx, member: discord.Member, amount: int):
        if await levelling.find_one({'guild': ctx.guild.id, "user": ctx.author.id}):
            await ctx.send("User has no account")
        else:
            await levelling.update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": amount}})
            await ctx.send(f"Successfully added {amount} xp to {member}")

    @commands.command(help="Remove xp from member")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_xp(self, ctx, member: discord.Member, amount: int):
        if await levelling.find_one({'guild': ctx.guild.id, "user": ctx.author.id}):
            await ctx.send("User has no account")
        else:
            await levelling.update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": -amount}})
            await ctx.send(f"Successfully remove {amount} xp from {member}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await roled.insert_one({"guild": guild.id, "role": [], "level": [],
                                "xp": 10})

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            results = await roled.find_one({"guild": guild.id})
            if results is None:
                await roled.insert_one({"guild": guild.id, "role": [], "level": [],
                                        "xp": 10})

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                result = await levelling.find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await levelling.delete_one({"guild": guild.id, "user": member.id})
        await roled.delete_one({"guild": guild.id})
        is_disabled = await disable.find_one({"guild": guild.id})
        if is_disabled is not None:
            await disable.delete_one(is_disabled)
        check = await upchannel.find_one({"guild": guild.id})
        if check is not None:
            await roled.delete_one({"guild": guild.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await levelling.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await levelling.delete_one({"guild": member.guild.id, "user": member.id})