import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
modlogdb = cluster["moderation"]
cursors = modlogdb['modlog']
cases = modlogdb['cases']


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
            await cases.update_one({"guild": ctx.guild.id}, {"$push": {"cases": {"Number": int(num_of_case), "user": f"{member}", "type": "warning", "Mod": f"{ctx.author}", "reason": str(reason)}}})
            await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

            result = await cursors.find_one({"guild": ctx.guild.id})
            if result is not None:
                channel = self.bot.get_channel(result["channel"])
                embed = discord.Embed(title=f"Case #{num_of_case}: Warn!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
                await channel.send(embed=embed)

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
        await cases.update_one({"guild": ctx.guild.id},
                               {"$push": {"cases": {"Number": int(num_of_case), "type": "mute", "user": f"{member}", "Mod": f"{ctx.author}", "reason": str(reason)}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: Mute!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
            await channel.send(embed=embed)

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
        await cases.update_one({"guild": ctx.guild.id},
                               {"$push": {"cases": {"Number": int(num_of_case), "type": "kick", "user": f"{member}", "Mod": f"{ctx.author}", "reason": str(reason)}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: Kick!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
            await channel.send(embed=embed)

    @commands.command(help="Ban member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if not member.bot:
            await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for {reason}. What a shame 👎")
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} has been **BANNED** for {reason}')

        num_of_case = (await cases.find_one({"guild": ctx.guild.id}))['num'] + 1
        await cases.update_one({"guild": ctx.guild.id},
                               {"$push": {"cases": {"Number": int(num_of_case), "type": "ban", "user": f"{member}", "Mod": f"{ctx.author}", "reason": str(reason)}}})
        await cases.update_one({"guild": ctx.guild.id}, {"$inc": {"num": 1}})

        result = await cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            channel = self.bot.get_channel(result["channel"])
            embed = discord.Embed(title=f"Case #{num_of_case}: Ban!", description=f"**User:** {member} **Mod:**{ctx.author} \n**Reason:** {reason}", color=discord.Color.red())
            await channel.send(embed=embed)

    @commands.command(help="Unban member")
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, *, member_id):
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

    @commands.command(help="Look at your server cases")
    async def caselist(self, ctx):
        results = await cases.find_one({"guild": ctx.guild.id})
        embed = discord.Embed(title=f"{ctx.guild.name} caselist", description=f"Total case: {results['num']}", color=discord.Color.red())
        if len(results['cases']) < 1:
            await ctx.send("Looks like all your server members are good people 🥰")
        for case in results['cases']:
            embed.add_field(name=f"Case {case['Number']}", value=f"**Type:** {case['type']}\n **User:** {case['user']}\n**Mod:**{case['Mod']}\n**Reason:** {case['reason']}")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            results = await cases.find_one({"guild": guild.id})
            if results is None:
                insert = {"guild": guild.id, "num": 0, "cases": []}
                await cases.insert_one(insert)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        insert = {"guild": guild.id, "num": 0, "cases": []}
        await cases.insert_one(insert)
