import nextcord as discord
from nextcord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
modlogdb = cluster["moderation"]
cursors = modlogdb['modlog']
cases = modlogdb['cases']
user_case = modlogdb['user']

timerdb = cluster["timer"]
timer = timerdb['mod']


def convert(time):
    pos = ['s', 'm', 'h', 'd']

    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}

    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2

    return val * time_dict[unit]


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Warn member")
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        guild = ctx.guild
        if reason is None:
            await ctx.send("You need a reason for this command to work")
        else:
            embed = discord.Embed(
                description=f'**⚠️ {member.mention} has been warned for: {reason}**',
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            emb = discord.Embed(description=f"You have been warned in **{guild.name}** for: **{reason}**", color=discord.Color.red())
            await member.send(embed=emb)

            num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
            await cases.update_one({"guild": ctx.guild.id}, {"$push": {"cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "warning", "Mod": f"{ctx.author.id}", "reason": str(reason)}}})
            await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

            result = await cursors.find_one({"guild": ctx.guild.id})
            if result is not None:
                channel = self.bot.get_channel(result["channel"])
                embed = discord.Embed(title=f"Case #{num_of_case}: Warn!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
                await channel.send(embed=embed)

            check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
            if check_user_case is None:
                await user_case.insert_one({"guild": ctx.guild.id, "user": member.id, "total_cases": 1})
            else:
                await user_case.update_one({"guild": ctx.guild.id, "user": member.id}, {"$inc": {"total_cases": 1}})

    @commands.command(help="Mute member")
    @commands.has_permissions(administrator=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name="DHB_muted")
        if not mutedRole:
            mutedRole = await guild.create_role(name="DHB_muted")

            for channel in guild.channels:
                await channel.set_permissions(mutedRole,
                                              speak=False,
                                              send_messages=False,
                                              read_message_history=True,
                                              read_messages=False)
        await member.add_roles(mutedRole, reason=reason)
        await ctx.send(f"Muted {member.mention} for reason {reason}")
        await member.send(f"You were muted in **{guild.name}** for {reason}")

        num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
        await cases.update_one({"guild": ctx.guild.id}, {"$push": {"cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "mute", "Mod": f"{ctx.author.id}", "reason": str(reason)}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: Mute!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
            await channel.send(embed=embed)

        check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
        if check_user_case is None:
            await user_case.insert_one({"guild": ctx.guild.id, "user": member.id, "total_cases": 1})
        else:
            await user_case.update_one({"guild": ctx.guild.id, "user": member.id}, {"$inc": {"total_cases": 1}})

    @commands.command(help="Mute member but with a timer")
    @commands.has_permissions(administrator=True)
    async def tempmute(self, ctx, member: discord.Member, time, *, reason=None):
        converted_time = convert(time)
        if converted_time == -1:
            await ctx.send("You didn't answer the time correctly")

        elif converted_time == -2:
            await ctx.send("Time must be an integer")
        else:
            guild = ctx.guild
            mutedRole = discord.utils.get(guild.roles, name="DHB_muted")
            if not mutedRole:
                mutedRole = await guild.create_role(name="DHB_muted")

                for channel in guild.channels:
                    await channel.set_permissions(mutedRole,
                                                  speak=False,
                                                  send_messages=False,
                                                  read_message_history=True,
                                                  read_messages=False)
            await member.add_roles(mutedRole, reason=reason)
            await ctx.send(f"Temporarily muted {member.mention} for reason {reason}")
            await member.send(f"You were muted for {converted_time} seconds in **{guild.name}** for {reason}")

            num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
            await cases.update_one({"guild": ctx.guild.id}, {"$push": {
                "cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "mute", "Mod": f"{ctx.author.id}",
                          "reason": str(reason)}}})
            await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

            result = await cursors.find_one({"guild": ctx.guild.id})
            if result is not None:
                channel = self.bot.get_channel(result["channel"])
                embed = discord.Embed(title=f"Case #{num_of_case}: Temporary Mute!",
                                      description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}",
                                      color=discord.Color.red())
                await channel.send(embed=embed)

            check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
            if check_user_case is None:
                await user_case.insert_one({"guild": ctx.guild.id, "user": member.id, "total_cases": 1})
            else:
                await user_case.update_one({"guild": ctx.guild.id, "user": member.id}, {"$inc": {"total_cases": 1}})

            current_time = datetime.datetime.now()
            final_time = current_time + datetime.timedelta(seconds=converted_time)
            await timer.insert_one({"guild": ctx.guild.id, "type": "mute", "time": final_time, "user": member.id, "role": mutedRole.id})

    @commands.command(help="Unmute member")
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx, member: discord.Member):
        mutedRole = discord.utils.get(ctx.guild.roles,
                                      name="DHB_muted")

        await member.remove_roles(mutedRole)
        await ctx.send(f"Unmuted {member.mention}")
        await member.send(f"You were unmuted in the **{ctx.guild.name}**. Make sure you behave well 😉")

    @commands.command(help="Kick member")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if not member.bot:
            await member.send(f"You've been kick from **{ctx.guild.name}** for {reason}")
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} has been kick for {reason}')

        num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
        await cases.update_one({"guild": ctx.guild.id}, {"$push": {"cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "kick", "Mod": f"{ctx.author.id}", "reason": str(reason)}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: Kick!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
            await channel.send(embed=embed)

        check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
        if check_user_case is None:
            await user_case.insert_one({"guild": ctx.guild.id, "user": member.id, "total_cases": 1})
        else:
            await user_case.update_one({"guild": ctx.guild.id, "user": member.id}, {"$inc": {"total_cases": 1}})

    @commands.command(help="Ban member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if not member.bot:
            await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for {reason}. What a shame 👎")
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} has been **BANNED** for {reason}')

        num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
        await cases.update_one({"guild": ctx.guild.id}, {"$push": {"cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "ban", "Mod": f"{ctx.author.id}", "reason": str(reason)}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: Ban!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
            await channel.send(embed=embed)

        check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
        if check_user_case is None:
            await user_case.insert_one({"guild": ctx.guild.id, "user": member.id, "total_cases": 1})
        else:
            await user_case.update_one({"guild": ctx.guild.id, "user": member.id}, {"$inc": {"total_cases": 1}})

    @commands.command(help="Ban member but temporarily")
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.User, time, *, reason=None):
        converted_time = convert(time)
        if converted_time == -1:
            await ctx.send("You didn't answer the time correctly")

        elif converted_time == -2:
            await ctx.send("Time must be an integer")
        else:
            if not member.bot:
                await member.send(
                    f"You've been banned for {converted_time} seconds from **{ctx.guild.name}** for {reason}. Don't worry, it will be a short time!!")
            await ctx.guild.ban(member)
            num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
            await cases.update_one({"guild": ctx.guild.id}, {"$push": {
                "cases": {"Number": int(num_of_case), "user": f"{member.id}", "type": "ban", "Mod": f"{ctx.author.id}",
                          "reason": str(reason)}}})
            await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

            result = await cursors.find_one({"guild": ctx.guild.id})
            if result is not None:
                channel = self.bot.get_channel(result["channel"])
                embed = discord.Embed(title=f"Case #{num_of_case}: Temporary Ban!",
                                      description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}",
                                      color=discord.Color.red())
                await channel.send(embed=embed)

            check_user_case = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
            if check_user_case is None:
                await user_case.insert_one({"guild": ctx.guild.id, "user": member.id, "total_cases": 1})
            else:
                await user_case.update_one({"guild": ctx.guild.id, "user": member.id}, {"$inc": {"total_cases": 1}})

            current_time = datetime.datetime.now()
            final_time = current_time + datetime.timedelta(seconds=converted_time)
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
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, *, member_id: int):
        await ctx.guild.unban(discord.Object(id=member_id))
        await ctx.send("Successfully unban him")

    @commands.command(help="Clear messages in a certain amount", aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount+1)

    @commands.command(help="Clear all messages in that channel")
    @commands.has_permissions(manage_messages=True)
    async def clear_all(self, ctx):
        await ctx.channel.purge(limit=None)

    @commands.command(help="Lock channel")
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send('Channel locked.')

    @commands.command(help="Unlock channel")
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send('Channel unlocked.')

    @commands.group(invoke_without_command=True, help="Modlog and case")
    async def modlog(self, ctx):
        await ctx.send("modlog channel: set up modlog channel\nmodlog remove: end modlog system")

    @modlog.command(help="Set up channel")
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            if result is None:
                insert = {"guild": ctx.guild.id, "channel": channel.id}
                await cursors.insert_one(insert)
                await ctx.send(f"Modlog channel set to {channel.mention}")
            elif result is not None:
                await cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
                await ctx.send(f"Modlog channel updated to {channel.mention}")

    @modlog.command(help="Remove modlog system if you like to")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            await cursors.delete_one(result)
            await ctx.send("Modlog system has been remove")
        else:
            await ctx.send("You don't have a Modlog channel")

    @commands.command(help="Look at your server cases", aliases=["case"])
    async def caselist(self, ctx, member: discord.Member = None):
        if member is None:
            results = await cases.find_one({"guild": ctx.guild.id})
            embed = discord.Embed(title=f"{ctx.guild.name} caselist", description=f"Total case: {results['num']}",
                                  color=discord.Color.red())
            if len(results['cases']) < 1:
                await ctx.send("Looks like all your server members are good people 🥰")
            for case in results['cases']:
                embed.add_field(name=f"Case {case['Number']}",
                                value=f"**Type:** {case['type']}\n **User:** {self.bot.get_user(int(case['user']))}\n**Mod:**{self.bot.get_user(int(case['Mod']))}\n**Reason:** {case['reason']}")
            await ctx.send(embed=embed)
        else:
            user_check = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
            if user_check is None:
                await ctx.send("Looks like a good person 🥰")
            else:
                embed = discord.Embed(title=f"{self.bot.get_user(int(user_check['user']))} cases", description=f"Total case: {user_check['total_cases']}", color=discord.Color.red())
                case_check = await cases.find_one({"guild": ctx.guild.id, "cases.user": f"{member.id}"})
                embed.add_field(name="List of cases", value=f"{case_check}")
                await ctx.send(embed=embed)

    @commands.command(help="Remove that member cases")
    @commands.has_permissions(administrator=True)
    async def forgive(self, ctx, member: discord.Member):
        user_check = await user_case.find_one({"guild": ctx.guild.id, "user": member.id})
        if user_check is None:
            await ctx.send("Looks like a good person already 🥰")
        else:
            await user_case.delete_one(user_check)
            await ctx.send("🕊 You forgive him!!")

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            results = await cases.find_one({"guild": guild.id})
            if results is None:
                insert = {"guild": guild.id, "num": 0, "cases": []}
                await cases.insert_one(insert)

        self.time_checker.start()

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

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await user_case.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await user_case.delete_one(result)