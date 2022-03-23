import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
from utils.imageUtils import get_image_from_url
from PIL import Image, ImageDraw, ImageFont
import io
from cogs.config.configuration import ConfigurationBase

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursors = cluster["welcome"]["channel"]


class Welcome(ConfigurationBase):
    @commands.group(invoke_without_command=True, case_insensitive=True, help="Welcome system setup")
    async def welcome(self, ctx):
        _cmd = self.bot.get_command("help")
        await _cmd(ctx, command='welcome')

    @welcome.command(help="Setup welcome channel")
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}",
                      "dm": f"Have fun at **{ctx.guild.name}**",
                      "img": "https://cdn.discordapp.com/attachments/875886792035946496/936446668293935204/bridge.png"}
            await cursors.insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        elif result is not None:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @welcome.command(help="Remove welcome system", aliases=['disable'])
    @commands.has_permissions(manage_channels=True)
    async def remove(self, ctx):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            await cursors.delete_one(result)
            await ctx.send("Welcome system has been remove")
        else:
            await ctx.send("You don't have a welcome system")

    @welcome.command(help="Create your welcome message. Use var to see the list of variables")
    @commands.has_permissions(manage_channels=True)
    async def text(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            if text.lower() == "var":
                return await ctx.send("""
    {mention}: Mention the joined user
    {username}: user name and discriminator
    {count}: Display the member count
    {name}: The user's name
    {server}: The server's name
                    """)
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
            await ctx.send(f"Welcome message updated to ```{text}```")

    @welcome.command(help="Setup welcome dm")
    @commands.has_permissions(manage_messages=True)
    async def dm(self, ctx, *, text):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
            await ctx.send(f"Welcome dm updated to ```{text}```")

    @welcome.command(help="Custom image. Make sure it's a link", aliases=["img"])
    @commands.has_permissions(manage_messages=True)
    async def image(self, ctx, *, link: str):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"img": link}})
            await ctx.send(f"Successfully updated welcome image")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        result = await cursors.find_one({"guild": member.guild.id})
        if result is None:
            return
        else:
            channel = self.bot.get_channel(result["channel"])

            image = Image.open(get_image_from_url(
                result['img'])).convert(
                "RGBA")

            image = image.resize((1024, 500))

            big_font = ImageFont.truetype("font.ttf", 36)
            small_font = ImageFont.truetype("font.ttf", 30)

            rectangle_image = Image.new('RGBA', (1024, 500))
            rectangle_draw = ImageDraw.Draw(rectangle_image)
            rectangle_draw.rectangle((30, 30, 994, 470), fill=(0, 0, 0, 127))

            image = Image.alpha_composite(image, rectangle_image)

            draw = ImageDraw.Draw(image, "RGBA")

            draw.text((512, 360), f"🎉 {member} just joined this server", fill=(255, 255, 255), font=big_font, anchor="ms")
            draw.text((512, 390), f"Member {member.guild.member_count}", fill=(255, 255, 255), font=small_font, anchor="ms")

            AVATAR_SIZE = 200
            avatar_asset = member.avatar.replace(format='jpg', size=128)
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

            image.paste(avatar_image, (400, 100), circle_image)

            buffer_output = io.BytesIO()
            image.save(buffer_output, format='PNG')
            buffer_output.seek(0)

            await channel.send(
                str(result["message"]).format(
                    mention=member.mention,
                    count=member.guild.member_count,
                    name=member.name,
                    guild=member.guild.name,
                    username=member
                ),
                file=discord.File(buffer_output, 'welcome.png')
            )
            if not member.bot:
                await member.send(
                    str(result["dm"]).format(
                        count=member.guild.member_count,
                        name=member.name,
                        guild=member.guild.name,
                        username=member
                    )
                )

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursors.find_one({"guild": guild.id})
        if result is not None:
            await cursors.delete_one({"guild": guild.id})
