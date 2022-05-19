import discord
from discord.ext import commands
import datetime
import asyncio


class ModLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_modlog(self, guild, type_off, target, mod, reason):
        num_of_case = (await self.bot.mongo["moderation"]['cases'].find_one({"guild": guild.id}))['num']
        await self.bot.mongo["moderation"]['cases'].update_one(
            {"guild": guild.id},
            {"$push": {
                "cases":
                    {"Number": int(num_of_case),
                     "user": f"{target}",
                     "user_id": target.id,
                     "type": type_off,
                     "Mod": f"{mod}",
                     "reason": str(reason),
                     "time": datetime.datetime.utcnow()}}}
        )
        await self.bot.mongo["moderation"]['cases'].update_one({"guild": guild.id}, {"$inc": {"num": 1}})

        result = await self.bot.mongo["moderation"]['modlog'].find_one({"guild": guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: {type_off.title()}!",
                                  description=f"**User:** {target} ({target.id}) \n**Mod:** {mod} ({mod.id})\n**Reason:** {reason}",
                                  color=discord.Color.red(),
                                  timestamp=datetime.datetime.utcnow())
            embed.set_footer(text=f"Moderator: {mod}", icon_url=mod.display_avatar.url)
            await channel.send(embed=embed)

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
