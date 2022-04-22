import discord
from discord.ext import commands
import datetime
import asyncio


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modlogChannel = self.bot.mongo["moderation"]['modlog']
        self.cases = self.bot.mongo["moderation"]['cases']
        self.userCase = self.bot.mongo["moderation"]['user']

    async def run_modlog(self, guild, type_off, target, mod, reason):
        num_of_case = (await self.cases.find_one({"guild": guild.id}))['num']
        await self.cases.update_one({"guild": guild.id}, {"$push": {
            "cases": {"Number": int(num_of_case), "user": f"{target.id}", "type": type_off, "Mod": f"{mod.id}",
                      "reason": str(reason), "time": datetime.datetime.utcnow()}}})
        await self.cases.update_one({"guild": guild.id}, {"$inc": {"num": 1}})

        result = await self.modlogChannel.find_one({"guild": guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: {type_off.title()}!",
                                  description=f"**User:** {target} ({target.id}) \n**Mod:** {mod} ({mod.id})\n**Reason:** {reason}",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.utcnow())
            embed.set_footer(text=f"Moderator: {mod}", icon_url=mod.avatar.url)
            await channel.send(embed=embed)

        if not target.bot:
            if type_off in ["ban", "kick", "unban"]:
                return
            check_user_case = await target.find_one({"guild": guild.id, "user": target.id})
            if check_user_case is None:
                return await self.userCase.insert_one({"guild": guild.id, "user": target.id, "total_cases": 1})
            await self.userCase.update_one({"guild": guild.id, "user": target.id}, {"$inc": {"total_cases": 1}})

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not guild.me.guild_permissions.view_audit_log:
            return
        await asyncio.sleep(2)
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=10):
            if entry.target == user:
                return await self.run_modlog(guild, "ban", user, entry.user, entry.reason)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if not guild.me.guild_permissions.view_audit_log:
            return
        await asyncio.sleep(2)
        async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=10):
            if entry.target == user:
                return await self.run_modlog(guild, "unban", user, entry.user, entry.reason)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.guild.me.guild_permissions.view_audit_log:
            return
        await asyncio.sleep(2)
        async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=10):
            if entry.target == member:
                return await self.run_modlog(member.guild, "kick", member, entry.user, entry.reason)
