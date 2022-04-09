import discord
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
from utils import has_mod_role, config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
modb = cluster["moderation"]
cursors = modb['modlog']
cases = modb['cases']
user_case = modb['user']
timer = cluster["timer"]['mod']
cursor = cluster["moderation"]['automod']


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


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time_checker.start()

    async def modlogUtils(self, ctx, criminal, type_off: str, reason: str):
        num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1

        embed = discord.Embed(title=f"Case {num_of_case}",
                              description=f"{criminal.mention} has been {type_off.title()}ed for: {reason}",
                              color=discord.Color.red(),
                              timestamp=ctx.message.created_at)
        embed.set_footer(text=f"Moderator: {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

        await cases.update_one({"guild": ctx.guild.id}, {"$push": {
            "cases": {"Number": int(num_of_case), "user": f"{criminal.id}", "type": type_off, "Mod": f"{ctx.author.id}",
                      "reason": str(reason), "time": datetime.datetime.utcnow()}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: {type_off.title()}!",
                                  description=f"**User:** {criminal} ({criminal.id}) \n**Mod:** {ctx.author} ({ctx.author.id})\n**Reason:** {reason}",
                                  color=discord.Color.red(),
                                  timestamp=ctx.message.created_at)
            embed.set_footer(text=f"Moderator: {ctx.author}", icon_url=ctx.author.avatar.url)
            await channel.send(embed=embed)

        if not criminal.bot:
            if "ban" or "kick" or "unban "not in type_off:
                check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": criminal.id})
                if check_user_case is None:
                    return await user_case.insert_one({"guild": ctx.guild.id, "user": criminal.id, "total_cases": 1})
                await user_case.update_one({"guild": ctx.guild.id, "user": criminal.id}, {"$inc": {"total_cases": 1}})

    @commands.command(help="Warn member")
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            return await ctx.send("You need a reason for this command to work")
        emb = discord.Embed(description=f"You have been warned in **{ctx.guild.name}** for: **{reason}**",
                            color=discord.Color.red())
        await member.send(embed=emb)
        await self.modlogUtils(ctx, member, "warn", reason)

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
        await member.edit(timeout=duration)

        await member.send(f"You were timeout in **{ctx.guild.name}** for **{reason}**")
        await self.modlogUtils(ctx, member, "timeout", reason)

    @commands.command(help="Untimeout a member")
    @commands.check_any(has_mod_role(), commands.has_permissions(moderate_members=True))
    async def untimeout(self, ctx, member: discord.Member, *, reason=None):
        await member.edit(timeout=None)
        await member.send(f"You were timeout in **{ctx.guild.name}** for **{reason}**")

        await self.modlogUtils(ctx, member, "untimeout", reason)

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
                                              speak=False,
                                              send_messages=False,
                                              read_message_history=True,
                                              read_messages=False)
        await member.add_roles(mutedRole, reason=reason)
        await self.modlogUtils(ctx, member, "mute", reason)

    @commands.command(help="Mute member but with a timer")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_roles=True))
    async def tempmute(self, ctx, member: discord.Member, time, *, reason=None):
        if ctx.author.top_role.position < member.top_role.position:
            return await ctx.send("You can't mute someone with a higher role than you")
        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")

        elif converted_time == -2:
            return await ctx.send("Time must be an integer")
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name="muted")
        if not mutedRole:
            mutedRole = await guild.create_role(name="muted")

            for channel in guild.channels:
                await channel.set_permissions(mutedRole,
                                              speak=False,
                                              send_messages=False,
                                              read_message_history=True,
                                              read_messages=False)
        await member.add_roles(mutedRole, reason=reason)
        final_time = datetime.datetime.now() + datetime.timedelta(seconds=converted_time)
        await member.send(
            f"You were temporarily muted for <t:{int(datetime.datetime.timestamp(final_time))}:R> in **{guild.name}** for **{reason}**")
        await timer.insert_one({"guild": ctx.guild.id, "type": "mute", "time": final_time, "user": member.id})
        await self.modlogUtils(ctx, member, "tempmute", reason)

    @commands.command(help="Unmute member")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_roles=True))
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        mutedRole = discord.utils.get(ctx.guild.roles,
                                      name="muted")

        await member.remove_roles(mutedRole)
        await member.send(f"You were unmuted in the **{ctx.guild.name}**. Make sure you behave well 😉")

        await self.modlogUtils(ctx, member, "unmute", reason)

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
            await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for **{reason}**. What a shame 👎")
        await member.ban(reason=reason)
        await self.modlogUtils(ctx, member, "ban", reason)

    @commands.command(help="Ban loads of people")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def massban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        for member in members:
            if ctx.author.top_role.position < member.top_role.position:
                return await ctx.send("You can't ban someone with a higher role than you")
            if not member.bot:
                await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for **{reason}**. What a shame 👎")
            await member.ban(reason=reason)
        await ctx.message.add_reaction("✅")

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
                f"You've been banned for <t:{int(datetime.datetime.timestamp(final_time))}:R> from **{ctx.guild.name}** for **{reason}**. Don't worry, it will be a short time!!")
        await ctx.guild.ban(member)
        await self.modlogUtils(ctx, member, "tempban", reason)
        await timer.insert_one({"guild": ctx.guild.id, "type": "ban", "time": final_time, "user": member.id})

    @tasks.loop(seconds=10)
    async def time_checker(self):
        try:
            all_timer = timer.find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    if x['type'] == "mute":
                        server = self.bot.get_guild(int(x['guild']))
                        member = server.get_member(int(x['user']))
                        mutedRole = server.get_role(int(x['role']))
                        await member.remove_roles(mutedRole)

                        await timer.delete_one({"user": member.id})
                    elif x['type'] == "ban":
                        server = self.bot.get_guild(int(x['guild']))
                        user = self.bot.get_user(int(x['user']))
                        await server.unban(user)

                        await timer.delete_one({"user": user.id})
                else:
                    pass
        except Exception as e:
            print(e)

    @commands.command(help="Unban member")
    @commands.check_any(has_mod_role(), commands.has_permissions(ban_members=True))
    async def unban(self, ctx, user_id: int, *, reason=None):
        user = self.bot.get_user(int(user_id))
        await ctx.guild.unban(user)

        await self.modlogUtils(ctx, user, "unban", reason)

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

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        insert = {"guild": guild.id, "num": 0, "cases": []}
        await cases.insert_one(insert)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await cases.delete_one({"guild": guild.id})
        channel_check = await cursors.find_one({"guild": guild.id})
        if channel_check is not None:
            await cursors.delete_one(channel_check)
        for member in guild.members:
            if not member.bot:
                result = await user_case.find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await user_case.delete_one(result)
        if await cursor.find_one({"guild": guild.id}) is not None:
            await cursor.delete_one({"guild": guild.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await user_case.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await user_case.delete_one(result)