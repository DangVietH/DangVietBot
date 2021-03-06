import discord
from discord.ext import commands
import datetime


def convert(time):
    pos = ['s', 'm', 'h', 'd']

    time_dict = {"s": 1 / 60, "m": (1 / 60) * 60, "h": ((1 / 60) * 60) * 60, "d": (((1 / 60) * 60) * 60) * 24}

    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2

    return val * time_dict[unit]


def has_mod_role():
    async def predicate(ctx):
        result = await ctx.bot.mongo["moderation"]['modrole'].find_one({"guild": ctx.guild.id})
        if result is None:
            return False
        if ctx.guild.get_role(result['role']) in ctx.author.roles:
            return True

    return commands.check(predicate)


class Moderation(commands.Cog):
    emoji = "<:mod:968445248252551178>"

    def __init__(self, bot):
        self.bot = bot

    async def modlogUtils(self, ctx, target, type_off: str, reason: str, logging=False):
        num_of_case = (await self.bot.mongo["moderation"]['cases'].find_one({"guild": ctx.guild.id}))['num'] + 1

        embed = discord.Embed(title=f"Case {num_of_case}",
                              description=f"{target.mention} has been {type_off.title()}ed for: {reason}",
                              color=discord.Color.red(),
                              timestamp=ctx.message.created_at)
        embed.set_footer(text=f"Moderator: {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        if logging is True:
            await self.bot.mongo["moderation"]['cases'].update_one({"guild": ctx.guild.id}, {"$push": {
                "cases": {
                    "Number": int(num_of_case),
                    "user": f"{target}",
                    "user_id": target.id,
                    "type": type_off,
                    "Mod": f"{ctx.author}",
                    "reason": str(reason),
                    "time": datetime.datetime.utcnow()}}})
            await self.bot.mongo["moderation"]['cases'].update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

            result = await self.bot.mongo["moderation"]['modlog'].find_one({"guild": ctx.guild.id})
            if result is not None:
                channel = self.bot.get_channel(result["channel"])
                embed = discord.Embed(title=f"Case #{num_of_case}: {type_off.title()}!",
                                      description=f"**User:** {target} ({target.id}) \n**Mod:** {ctx.author} ({ctx.author.id})\n**Reason:** {reason}",
                                      color=discord.Color.red(),
                                      timestamp=ctx.message.created_at)
                embed.set_footer(text=f"Moderator: {ctx.author}", icon_url=ctx.author.display_avatar.url)
                await channel.send(embed=embed)

            if not target.bot:
                if type_off in ["ban", "kick", "unban"]:
                    return
                check_user_case = await self.bot.mongo["moderation"]['user'].find_one({"guild": ctx.guild.id, "user": target.id})
                if check_user_case is None:
                    return await self.bot.mongo["moderation"]['user'].insert_one({"guild": ctx.guild.id, "user": target.id, "total_cases": 1})
                await self.bot.mongo["moderation"]['user'].update_one({"guild": ctx.guild.id, "user": target.id}, {"$inc": {"total_cases": 1}})

    @commands.command(help="Warn member")
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            return await ctx.send("You need a reason for this command to work")
        emb = discord.Embed(description=f"You have been warned in **{ctx.guild.name}** for: **{reason}**",
                            color=discord.Color.red())
        await member.send(embed=emb)
        await self.modlogUtils(ctx, member, "warn", reason, logging=True)

    @commands.command(help="Timeout a member")
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def timeout(self, ctx, member: discord.Member, time, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't timeout someone with a higher role than you")
        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")
        elif converted_time == -2:
            return await ctx.send("Time must be an integer")
        duration = datetime.timedelta(minutes=converted_time)
        await member.timeout(duration, reason=reason)

        await member.send(f"You were timeout in **{ctx.guild.name}** for **{reason}**")
        await self.modlogUtils(ctx, member, "timeout", reason, logging=True)

    @commands.command(help="Untimeout a member")
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def untimeout(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(timed_out_until=None)
        await member.send(f"You were timeout in **{ctx.guild.name}** for **{reason}**")
        await self.modlogUtils(ctx, member, "untimeout", reason, logging=True)

    @commands.command(help="Mute member")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_roles=True))
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't mute someone with a higher role than you")
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name="muted")
        if not mutedRole:
            mutedRole = await guild.create_role(name="muted")

            for channel in guild.channels:
                await channel.set_permissions(mutedRole,
                                              send_messages=False,
                                              add_reactions=False)
        await member.add_roles(mutedRole, reason=reason)
        await self.modlogUtils(ctx, member, "mute", reason, logging=True)

    @commands.command(help="Unmute member")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_roles=True))
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        mutedRole = discord.utils.get(ctx.guild.roles,
                                      name="muted")

        await member.remove_roles(mutedRole)
        await member.send(f"You were unmuted in the **{ctx.guild.name}**. Make sure you behave well ????")
        await self.modlogUtils(ctx, member, "unmute", reason, logging=True)

    @commands.command(help="Kick member")
    @commands.check_any(has_mod_role(), commands.has_permissions(kick_members=True))
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't kick someone with a higher role than you")
        if not member.bot:
            await member.send(f"You've been kick from **{ctx.guild.name}** for **{reason}**")
        await member.kick(reason=reason)
        await self.modlogUtils(ctx, member, "kick", reason)

    @commands.command(help="Ban member")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't ban someone with a higher role than you")
        if not member.bot:
            await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for **{reason}**. What a shame ????")
        await member.ban(reason=reason)
        await self.modlogUtils(ctx, member, "ban", reason)

    @commands.command(help="Ban member but to clear chat")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def softban(self, ctx, member: discord.Member, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't ban someone with a higher role than you")
        await member.ban(reason=reason)
        await ctx.guild.unban(member, reason=reason)
        await self.modlogUtils(ctx, member, "softban", reason)

    @commands.command(help="Fuck the raiders")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def massban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        for member in members:
            if ctx.author.top_role.position < member.top_role.position:
                return await ctx.send("You can't ban someone with a higher role than you")
            if not member.bot:
                await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for **{reason}**. What a shame ????")
            await member.ban(reason=reason)
        await ctx.message.add_reaction("???")

    @commands.command(help="Ban member but temporarily")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def tempban(self, ctx, member: discord.User, time, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't ban someone with a higher role than you")
        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")

        elif converted_time == -2:
            return await ctx.send("Time must be an integer")
        final_time = datetime.datetime.now() + datetime.timedelta(seconds=converted_time)
        if not member.bot:
            await member.send(
                f"You've been banned for <t:{int(datetime.datetime.timestamp(final_time))}:R> from **{ctx.guild.name}** for **{reason}**!")
        await member.ban(reason=reason)
        await self.bot.mongo["timer"]['mod'].insert_one({"guild": ctx.guild.id, "type": "ban", "time": final_time, "user": member.id})
        await self.modlogUtils(ctx, member, "tempban", reason)

    @commands.command(help="Unban member")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def unban(self, ctx, user_id: int, *, reason=None):
        await ctx.guild.unban(discord.Object(id=user_id), reason=reason)
        await ctx.send("User unbaned")

    @commands.command(help="Clear messages in a certain amount", aliases=['purge'])
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_messages=True))
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)

    @commands.command(help="Lock channel")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send('Channel locked.')

    @commands.command(help="Unlock channel")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send('Channel unlocked.')

    @commands.command(help="Lock all channel")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def lock_all(self, ctx):
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(ctx.guild.default_role, send_messages=False)

    @commands.command(help="Unlock all channel")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def unlock_all(self, ctx):
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(ctx.guild.default_role, send_messages=True)