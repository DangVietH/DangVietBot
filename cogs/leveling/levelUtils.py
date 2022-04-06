import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils import config_var, SecondPageSource, MenuPages, has_mod_role

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

    async def add_to_db(self, guild):
        results = await levelConfig.find_one({"guild": guild.id})
        if results is None:
            await levelConfig.insert_one({"guild": guild.id, "role": [], "level": [], "xp": 10,
                                          "msg": "🎉 {mention} has reached level **{level}**!!🎉"})

    @commands.command(help="Set background for your server rank")
    async def setbackground(self, ctx, link):
        if await image_cursor.find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is not None:
            await image_cursor.update_one({"guild": ctx.guild.id, "member": ctx.author.id}, {"$set": {"image": link}})
        else:
            await image_cursor.insert_one({"guild": ctx.guild.id, "member": ctx.author.id, "image": link})
        await ctx.send("New Background set")

    @commands.command(help="Set background back to default")
    async def resetbackground(self, ctx):
        if await image_cursor.find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is None:
            await ctx.send("You don't have a custom background")
        await image_cursor.delete_one({"guild": ctx.guild.id, "member": ctx.author.id})
        await ctx.send("👍")

    @commands.check_any(has_mod_role(), commands.has_permissions(manage_messages=True))
    @commands.command(help="Set xp for each msg")
    async def setXpPermessage(self, ctx, level: int):
        await self.add_to_db(ctx.guild)
        await levelConfig.update_one({"guild": ctx.guild.id}, {"$set": {"xp": level}})
        await ctx.send(f"Xp per message set to {level}")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Level utils")
    async def lvl(self, ctx):
        await ctx.send_help(ctx.command)

    @lvl.command(help="Custom level up message. Use welcome text var to see the list of variables")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_messages=True))
    async def text(self, ctx, *, text):
        if text.lower() == "var":
            return await ctx.send("""
{mention}: Mention the joined user
{username}: user name and discriminator
{name}: The user's name
{server}: The server's name
                        """)
        await levelConfig.update_one({"guild": ctx.guild.id}, {"$set": {"msg": text}})
        await ctx.send(f"Welcome message updated to ```{text}```")

    @lvl.group(invoke_without_command=True, case_insensitive=True, help="Level rewarding role setup")
    async def role(self, ctx):
        await ctx.send_help(ctx.command)

    @role.command(help="Set up the roles")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def add(self, ctx, level: int, roles: discord.Role):
        role_cursor = await levelConfig.find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            await ctx.send("That role is already added")
        else:
            await levelConfig.update_one({"guild": ctx.guild.id}, {"$push": {"role": roles.id, "level": level}})
            await ctx.send(f"{roles.name} role added.")

    @role.command(help="Remove the role from level")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def remove(self, ctx, level: int, roles: discord.Role):
        role_cursor = await levelConfig.find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            await levelConfig.update_one({"guild": ctx.guild.id}, {"$pull": {"role": roles.id, "level": level}})
            await ctx.send(f"{roles.name} role remove.")
        else:
            await ctx.send("I don't remember I put that role in. do role list to see")

    @role.command(help="See list of rewarding roles")
    async def list(self, ctx):
        role_cursor = await levelConfig.find_one({"guild": ctx.guild.id})
        levelrole = role_cursor['role']
        levelnum = role_cursor['level']
        data = []
        for i in range(len(levelrole)):
            data.append((f"Level **{levelnum[i]}** role reward", ctx.guild.get_role(levelrole[i]).mention))
        page = MenuPages(source=SecondPageSource(f"{ctx.author.guild.name} role rewards", data),
                         clear_reactions_after=True)
        await page.start(ctx)

    @lvl.command(help="Setup level up channel if you like to")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def setchannel(self, ctx, channel: discord.TextChannel):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await upchannel.insert_one(insert)
            await ctx.send(f"Level up channel set to {channel.mention}")
        elif result is not None:
            await upchannel.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Level up channel updated to {channel.mention}")

    @lvl.command(help="Remove level up channel")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def removechannel(self, ctx):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a level up channel")
        else:
            await upchannel.delete_one(result)

    @lvl.command(help="Disable levelling")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_guild=True))
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
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_guild=True))
    async def renable(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await disable.delete_one(check)
            await ctx.send('Levelling re-enable')
        else:
            await ctx.send('Leveling already enabled')

    @commands.command(help="Add xp to member")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def add_xp(self, ctx, member: discord.Member, amount: int):
        if await levelling.find_one({'guild': ctx.guild.id, "user": ctx.author.id}) is None:
            return await ctx.send("User has no account")
        await levelling.update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": amount}})
        await ctx.send(f"Successfully added {amount} xp to {member}")

    @commands.command(help="Remove xp from member")
    @commands.check_any(has_mod_role(), commands.has_permissions(manage_channels=True))
    async def remove_xp(self, ctx, member: discord.Member, amount: int):
        if await levelling.find_one({'guild': ctx.guild.id, "user": ctx.author.id}) is None:
            return await ctx.send("User has no account")

        await levelling.update_one({'guild': ctx.guild.id, "user": ctx.author.id}, {"$inc": {"xp": -amount}})
        await ctx.send(f"Successfully remove {amount} xp from {member}")
