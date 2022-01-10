import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var
from datetime import datetime

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["moderation"]['automod']
cases = cluster["moderation"]['cases']
mchannel = cluster["moderation"]['modlog']


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
            if check['anti alt'] == "on":
                if not member.bot:
                    created = member.created_at
                    now = datetime.now()
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

                        await member.send("It's seems you're an alt by your account age!")
                        await member.kick(reason="Potential alt")