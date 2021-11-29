import discord
from discord.ext import commands


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

    @commands.command(help="Ban member")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if not member.bot:
            await member.send(f"You've been **BANNED** from **{ctx.guild.name}** for {reason}. What a shame 👎")
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} has been **BANNED** for {reason}')

    @commands.command(help="Unban member")
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split("#")

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.mention}')
                return

    @commands.command(help="Clear messages in a certain amount", aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount+1)

    @commands.command(help="Clear all messages in that channel")
    @commands.has_permissions(manage_messages=True)
    async def clear_all(self, ctx, amount=None):
        await ctx.channel.purge(limit=amount)

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
