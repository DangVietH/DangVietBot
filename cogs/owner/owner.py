import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])

cursor = cluster['bot']['blacklist']

ecursor = cluster["economy"]["users"]

levelling = cluster["levelling"]['member']


class Owner(commands.Cog):
    """Only DvH can use it"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Load a cog")
    @commands.is_owner()
    async def load(self, ctx, *, cog):
        try:
            self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('👌')

    @commands.command(help="Unload a cog")
    @commands.is_owner()
    async def unload(self, ctx, *, cog):
        try:
            self.bot.unload_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('👌')

    @commands.command(help="Reload a cog")
    @commands.is_owner()
    async def reload(self, ctx, *, cog):
        try:
            self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('👌')

    @commands.is_owner()
    @commands.command(help="Change the bot status")
    async def setstatus(self, ctx, presence, *, msg):
        if presence == "game":
            await self.bot.change_presence(activity=discord.Game(name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        elif presence == "watch":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        elif presence == "listen":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users))))
        elif presence == "stream":
            await self.bot.change_presence(activity=discord.Streaming(name=str(msg).format(server=len(self.bot.guilds), user=len(self.bot.users)), url="https://www.twitch.tv/dvieth"))
        else:
            await ctx.send('Invalid status')
        await ctx.message.add_reaction('👌')

    @commands.group(help="Blacklist ppls")
    @commands.is_owner()
    async def blacklist(self, ctx):
        embed = discord.Embed(title="Blacklist", color=discord.Color.random(), description="Create reaction roles")
        command = self.bot.get_command("blacklist")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"blacklist {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @blacklist.command(help="Blacklist user")
    @commands.is_owner()
    async def user(self, ctx, user: discord.User):
        check = await cursor.find_one({"id": user.id})
        if check is None:
            if await ecursor.find_one({"id": user.id}) is not None:
                await ecursor.delete_one({"id": user.id})

            if await levelling.find_one({"user": user.id}) is not None:
                await levelling.delete_one({"user": user.id})

            await user.send("You have been blacklisted")

            for guild in self.bot.guilds:
                if guild.owner.id == user.id:
                    await guild.system_channel.send("Leave this server because the owner is blacklisted")

            await cursor.insert_one({"id": user.id})
            await ctx.send("Blacklist user successfully")
        else:
            await ctx.send("User already blacklist")

    @commands.command(help="unBlacklist user")
    @commands.is_owner()
    async def unblacklist(self, ctx, user: discord.User):
        await cursor.delete_one({"id": user.id})
        await ctx.send("Unblacklist user successfully")