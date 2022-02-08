import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var
from datetime import timezone, datetime
import asyncio
import re

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["moderation"]['automod']
cases = cluster["moderation"]['cases']
mchannel = cluster["moderation"]['modlog']


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invite = re.compile(r'((http(s|):\/\/|)(discord)(\.(gg|io|me)\/|app\.com\/invite\/)([0-z]+))')
        self.links = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            data = await cursor.find_one({"guild": message.guild.id})
            if data is None:
                return
            else:
                if message.author.bot or message.author.guild_permissions.administrator is True:
                    return
                else:
                    check2 = await cursor.find_one({"guild": message.guild.id, "blacklist": message.content.lower()})
                    if check2 is not None:
                        await message.delete()
                        await message.author.send("That's a blacklisted word")
                    # anti invite 
                    if data['anti invite'] == "on":
                        if self.invite.findall(message.content) is True:
                            await message.delete()
                            await message.author.send("You cannot send invite links in this server")

                    # anti spam 
                    if data['anti spam'] == "on":
                        def check(m):
                            return m.author == message.author and (datetime.utcnow() - m.created_at.replace(tzinfo=None)).seconds < 5

                        if message.author.guild_permissions.administrator:
                            return
                        if len(list(filter(lambda m: check(m), self.bot.cached_messages))) >= 3:
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
                            await message.channel.purge(limit=8)
                            await message.channel.send(f"Temporally mute {message.author.mention} for spamming",
                                                       delete_after=5)
                            await asyncio.sleep(60)
                            await message.author.send("I unmuted you. Now BEHAVE OK!")

                    # anti link
                    if data['anti link'] == "on":
                        if re.findall(self.links, message.content) is True:
                            await message.delete()
                            await message.author.send("You cannot send links in this server")

                    if data['anti mass mention'] == "on":
                        if len(message.mentions) >= 3:
                            await message.delete()
                            await message.channel.send("There's a mass ping. Do something mods")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        check = await cursor.find_one({"guild": member.guild.id})
        if check is None:
            return
        else:
            if check['anti alt'] == "on":
                if not member.bot:
                    created = member.created_at
                    now = datetime.now(timezone.utc)
                    delta = (now - created).days
                    if delta <= 10:
                        num_of_case = (await cases.find_one({"guild": member.guild.id}))['num'] + 1
                        await cases.update_one({"guild": member.guild.id}, {"$push": {
                            "cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "kick",
                                      "Mod": f"{875589545532485682}", "reason": "Potential alt"}}})
                        await cases.update_one({"guild": member.guild.id}, {"$inc": {"num": 1}})

                        result = await mchannel.find_one({"guild": member.guild.id})
                        if result is not None:
                            channel = self.bot.get_channel(result["channel"])
                            embed = discord.Embed(title=f"Case #{num_of_case}: Kick!",
                                                  description=f"**User:** {member} **Mod:** DHB#6074 \n**Reason:** Potential alt",
                                                  color=discord.Color.red())
                            await channel.send(embed=embed)

                        await member.send("Because of your account age, you're kicked because you can be an alt!")
                        await member.kick(reason="Potential alt")
