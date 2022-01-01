import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var
import string
import random
import discapty
import asyncio

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["moderation"]['automod']


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

    @commands.Cog.listener(name="on_message")
    async def is_blacklist(self, message: discord.Message):
        if message.guild:
            check = await cursor.find_one({"guild": message.guild.id})
            if check is None:
                return
            else:
                check2 = await cursor.find_one({"guild": message.guild.id, "blacklist": message.content.lower()})
                if check2 is not None:
                    await message.delete()
                    await message.author.send("That's a blacklisted word")

    @commands.Cog.listener(name="on_message")
    async def anti_invite(self, message: discord.Message):
        if message.guild:
            if not message.author.bot:
                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
                    if "discord.gg" in message.content.lower():
                        if check['anti invite'] == "on":
                            await message.delete()
                            await message.author.send("You cannot send invite links in this server")
                    elif "discord.com/invite" in message.content.lower():
                        if check['anti invite'] == "on":
                            await message.delete()
                            await message.author.send("You cannot send invite links in this server")

    @commands.Cog.listener(name="on_message")
    async def anti_link(self, message: discord.Message):
        if message.guild:
            if not message.author.bot:
                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
                    if "https://" in message.content.lower():
                        if check['anti link'] == "on":
                            await message.delete()
                            await message.author.send("You cannot send links in this server")
                    elif "http://" in message.content.lower():
                        if check['anti link'] == "on":
                            await message.delete()
                            await message.author.send("You cannot send links in this server")

    @commands.Cog.listener(name="on_message")
    async def anti_mass_ping(self, message: discord.Message):
        if message.guild:
            if not message.author.bot:
                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
                    if len(message.mentions) > 3:
                        if check['anti mass mention'] == "on":
                            await message.delete()
                            await message.channel.send("There's a mass ping. Do something mods")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        check = await cursor.find_one({"guild": member.guild.id})
        if check is None:
            return
        else:
            if check['anti raid'] == "on":
                if not member.bot:
                    embed = discord.Embed(title=f"Hello {member}",
                                          description="This server has anti raid enabled! If you don't pass this test, you'll get kicked! \n**NOTE THIS IS CASE SENSITIVE**",
                                          color=discord.Color.red())
                    embed.set_footer(text="Complete this in 30 seconds")

                    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
                    random.shuffle(characters)

                    password = []
                    for i in range(10):
                        password.append(random.choice(characters))
                    random.shuffle(password)

                    c = "".join(password)
                    captcha = discapty.Captcha(c)
                    captcha_image = discord.File(captcha.generate_captcha(), filename="captcha.png")
                    await member.send(embed=embed, file=captcha_image)
                    try:
                        message = await self.bot.wait_for('message', timeout=30.0)
                    except asyncio.TimeoutError:
                        await member.send("You FAILED the test. Now you get kicked for being a raider")
                        await member.kick(reason="Potential Raider")
                    else:
                        if message.content == c:
                            await member.send("You have past the test. Now you're in")
                            await member.kick(reason="Potential Raider")
                        else:
                            await member.send("You FAILED the test. Now you get kicked for being a raider")
                            await member.kick(reason="Potential Raider")