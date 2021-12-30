import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import asyncio

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
cursor = cluster["moderation"]['automod']


class AutoModEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    async def anti_spam(self, message: discord.Message):
        if message.guild:
            message_cooldown = commands.CooldownMapping.from_cooldown(1.0, 5.0, commands.BucketType.user)
            bucket = message_cooldown.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            if retry_after:

                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
                    if check['anti spam'] == "on":
                        await message.channel.purge(after=datetime.datetime.now() - datetime.timedelta(hours=1),
                                                    check=lambda x: x.author.id == message.author.id,
                                                    oldest_first=False)
                        mutedRole = discord.utils.get(message.guild.roles, name="DHB_muted")
                        if not mutedRole:
                            mutedRole = await message.guild.create_role(name="DHB_muted")

                            for channel in message.guild.channels:
                                await channel.set_permissions(mutedRole,
                                                              speak=False,
                                                              send_messages=False,
                                                              read_message_history=True,
                                                              read_messages=False)
                        await message.author.add_roles(mutedRole, reason="spam")
                        await message.channel.send(f"Stop spamming {message.author.mention}")
                        await asyncio.sleep(10)
                        await message.author.remove_roles(mutedRole)
            else:
                return None

    @commands.Cog.listener(name="on_message")
    async def anti_invite(self, message: discord.Message):
        if message.guild:
            if "discord.gg" or "discord.com/invite" in message.content.lower():
                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
                    if check['anti invite'] == "on":
                        await message.delete()
                        await message.author.send("You cannot send invite links in this server")

    @commands.Cog.listener(name="on_message")
    async def anti_link(self, message: discord.Message):
        if message.guild:
            if "https://" or "https://" or "www." in message.content.lower():
                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
                    if check['anti link'] == "on":
                        await message.delete()
                        await message.author.send("You cannot send links in this server")

    @commands.Cog.listener(name="on_message")
    async def anti_mass_ping(self, message: discord.Message):
        if message.guild:
            if len(message.mentions) > 3:
                check = await cursor.find_one({"guild": message.guild.id})
                if check is None:
                    return
                else:
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
                return 