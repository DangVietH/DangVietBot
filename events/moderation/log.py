import discord
import datetime
from discord.ext import commands


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modlogChannel = self.bot.mongo["moderation"]['modlog']
        self.cases = self.bot.mongo["moderation"]['cases']
        self.userCase = self.bot.mongo["moderation"]['user']

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not guild.me.guild_permissions.view_audit_log:
            return
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.target.id == user.id:
                num_of_case = (await self.cases.find_one({"guild": guild.id}))['num'] + 1
                await self.cases.update_one({"guild": guild.id}, {"$push": {
                    "cases": {"Number": int(num_of_case), "user": f"{user.id}", "type": "ban",
                              "Mod": f"{entry.user.id}",
                              "reason": entry.reason if entry.reason else None,
                              "time": datetime.datetime.utcnow()}}})
                await self.cases.update_one({"guild": guild.id}, {"$inc": {"num": 1}})

                if await self.modlogChannel.find_one({"guild": guild.id}):
                    channel = self.bot.get_channel(
                        int((await self.modlogChannel.find_one({"guild": guild.id}))['channel']))
                    embed = discord.Embed(title=f"Case #{num_of_case}: BAN!",
                                          description=f"**User:** {user} ({user.id}) \n**Mod:** {entry.user} ({entry.user.id})\n**Reason:** {entry.reason if entry.reason else None}",
                                          color=discord.Color.red(),
                                          timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text=f"Moderator: {entry.user}", icon_url=entry.user.avatar.url)
                    await channel.send(embed=embed)
                    break

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if not guild.me.guild_permissions.view_audit_log:
            return
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.target.id == user.id:
                num_of_case = (await self.cases.find_one({"guild": guild.id}))['num'] + 1
                await self.cases.update_one({"guild": guild.id}, {"$push": {
                    "cases": {"Number": int(num_of_case), "user": f"{user.id}", "type": "unban",
                              "Mod": f"{entry.user.id}",
                              "reason": entry.reason if entry.reason else None,
                              "time": datetime.datetime.utcnow()}}})
                await self.cases.update_one({"guild": guild.id}, {"$inc": {"num": 1}})

                if await self.modlogChannel.find_one({"guild": guild.id}):
                    channel = self.bot.get_channel(
                        int((await self.modlogChannel.find_one({"guild": guild.id}))['channel']))
                    embed = discord.Embed(title=f"Case #{num_of_case}: Unban!",
                                          description=f"**User:** {user} ({user.id}) \n**Mod:** {entry.user} ({entry.user.id})\n**Reason:** {entry.reason if entry.reason else None}",
                                          color=discord.Color.red(),
                                          timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text=f"Moderator: {entry.user}", icon_url=entry.user.avatar.url)
                    await channel.send(embed=embed)
                    break
