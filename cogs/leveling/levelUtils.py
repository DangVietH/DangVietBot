import nextcord as discord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var


cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["levelling"]
levelling = db['member']
disable = db['disable']
levelConfig = db['roles']
upchannel = db['channel']
image_cursor = db['image']


class LevelUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Set background for your server rank")
    @commands.guild_only()
    async def setbackground(self, ctx, link):
        if await image_cursor.find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is not None:
            await image_cursor.update_one({"guild": ctx.guild.id, "member": ctx.author.id}, {"$set": {"image": link}})
        else:
            await image_cursor.insert_one({"guild": ctx.guild.id, "member": ctx.author.id, "image": link})
        await ctx.send("New Background set")

    @commands.command(help="Set background back to default")
    @commands.guild_only()
    async def resetbackground(self, ctx):
        if await image_cursor.find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is None:
            await ctx.send("You don't have a custom background")
        await image_cursor.delete_one({"guild": ctx.guild.id, "member": ctx.author.id})
        await ctx.send("👍")

    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setXpPermessage(self, ctx, level: int):
        await levelConfig.update_one({"guild": ctx.guild.id}, {"$set": {"xp": level}})
        await ctx.send(f"Xp per message set to {level}")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Level rewarding role setup")
    async def role(self, ctx):
        embed = discord.Embed(title="Level rewarding role setup", color=discord.Color.random())
        command = self.bot.get_command("role")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"role {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        embed.set_footer(text="Who needs MEE6 premium when we have this")
        await ctx.send(embed=embed)

    @role.command(help="Set up the roles")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add(self, ctx, level: int, roles: discord.Role):
        role_cursor = await levelConfig.find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            await ctx.send("That role is already added")
        else:
            await levelConfig.update_one({"guild": ctx.guild.id}, {"$push": {"role": roles.id, "level": level}})
            await ctx.send(f"{roles.name} role added.")

    @role.command(help="Remove the role from level")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove(self, ctx, level: int, roles: discord.Role):
        role_cursor = await levelConfig.find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            await levelConfig.update_one({"guild": ctx.guild.id}, {"$pull": {"role": roles.id, "level": level}})
            await ctx.send(f"{roles.name} role remove.")
        else:
            await ctx.send("I don't remember I put that role in. do role list to see")

    @role.command(help="See list of rewarding roles")
    @commands.guild_only()
    async def list(self, ctx):
        role_cursor = await levelConfig.find_one({"guild": ctx.guild.id})
        levelrole = role_cursor['role']
        levelnum = role_cursor['level']
        embed = discord.Embed(title="Role Rewards")
        for i in range(len(levelrole)):
            embed.add_field(name=f"Level {levelnum[i]}", value=f"Role reward: {ctx.guild.get_role(levelrole[i]).name}")
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Level channel setup")
    async def lvl(self, ctx):
        embed = discord.Embed(title="Level up utils", color=discord.Color.random())
        command = self.bot.get_command("lvl")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"lvl {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @lvl.command(help="Setup level up channel if you like to")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def set(self, ctx, channel: discord.TextChannel):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await upchannel.insert_one(insert)
            await ctx.send(f"Level up channel set to {channel.mention}")
        elif result is not None:
            await upchannel.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Level up channel updated to {channel.mention}")

    @lvl.command(help="Remove level up channel")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove(self, ctx):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a level up channel")
        else:
            await upchannel.delete_one(result)

    @lvl.command(help="Disable levelling")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def disable(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await ctx.send("Bruh")
        else:
            insert = {"guild": ctx.guild.id}
            await disable.insert_one(insert)
            for member in ctx.guild.members:
                if not member.bot:
                    result = await levelling.find_one({"guild": ctx.guild.id, "user": member.id})
                    if result is not None:
                        await levelling.delete_one({"guild": ctx.guild.id, "user": member.id})
            await ctx.send('Levelling disabled')

    @lvl.command(help="Re-enable levelling")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def renable(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await disable.delete_one(check)
            await ctx.send('Levelling re-enable')
        else:
            await ctx.send('Leveling already enabled')

    @commands.command(help="Add xp to member")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add_xp(self, ctx, member: discord.Member, amount: int):
        if await levelling.find_one({'guild': ctx.guild.id, "user": ctx.author.id}) is None:
            return await ctx.send("User has no account")
        await levelling.update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": amount}})
        await ctx.send(f"Successfully added {amount} xp to {member}")

    @commands.command(help="Remove xp from member")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_xp(self, ctx, member: discord.Member, amount: int):
        if await levelling.find_one({'guild': ctx.guild.id, "user": ctx.author.id}) is None:
            return await ctx.send("User has no account")

        await levelling.update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": -amount}})
        await ctx.send(f"Successfully remove {amount} xp from {member}")