import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])

welcome_cursors = cluster["welcome"]["channel"]

pcursor = cluster["custom_prefix"]["prefix"]

rcursor = cluster["react_role"]['reaction_roles']

gcursor = cluster['bot']['gc']

scursor = cluster['sb']['config']


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Welcome system setup")
    async def welcome(self, ctx):
        embed = discord.Embed(title="Welcome", color=discord.Color.random(), description="Set up welcome system")
        command = self.bot.get_command("welcome")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"welcome {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @welcome.command(help="Setup welcome channel")
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}",
                      "dm": f"Have fun at **{ctx.guild.name}**", "img": "https://cdn.discordapp.com/attachments/875886792035946496/936446668293935204/bridge.png"}
            await welcome_cursors.insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        elif result is not None:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @welcome.command(help="Remove welcome system", aliases=['disable'])
    @commands.has_permissions(manage_channels=True)
    async def remove(self, ctx):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            await welcome_cursors.delete_one(result)
            await ctx.send("Welcome system has been remove")
        else:
            await ctx.send("You don't have a welcome system")

    @welcome.command(help="Create your welcome message. Use var to see the list of variables")
    @commands.has_permissions(manage_channels=True)
    async def text(self, ctx, *, text):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            if text.lower() == "var":
                return await ctx.send("""
{mention}: Mention the joined user
{username}: user name and discriminator
{count}: Display the member count
{name}: The user's name
{server}: The server's name
                """)
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
            await ctx.send(f"Welcome message updated to ```{text}```")

    @welcome.command(help="Setup welcome dm")
    @commands.has_permissions(manage_messages=True)
    async def dm(self, ctx, *, text):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
            await ctx.send(f"Welcome dm updated to ```{text}```")

    @welcome.command(help="Custom image. Make sure it's a link", aliases=["img"])
    @commands.has_permissions(manage_messages=True)
    async def image(self, ctx, *, link: str):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"img": link}})
            await ctx.send(f"Successfully updated welcome image")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Custom prefix setup")
    async def prefix(self, ctx):
        embed = discord.Embed(title="Prefix", color=discord.Color.random(), description="Set up custom prefix")
        command = self.bot.get_command("prefix")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"prefix {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @prefix.command(help="Set custom prefix")
    @commands.has_permissions(manage_guild=True)
    async def set(self, ctx, *, prefixes):
        result = await pcursor.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "prefix": f"{prefixes}"}
            await pcursor.insert_one(insert)
            await ctx.send(f"Server prefix set to `{prefixes}`")
        elif result is not None:
            await pcursor.update_one({"guild": ctx.guild.id}, {"$set": {"prefix": f"{prefixes}"}})
            await ctx.send(f"Server prefix update to `{prefixes}`")

    @prefix.command(help="Set prefix back to default")
    @commands.has_permissions(manage_guild=True)
    async def remove(self, ctx):
        result = await pcursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a custom prefix yet")
        elif result is not None:
            await pcursor.delete_one(result)
            await ctx.send(f"Server prefix set back to default")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Reaction role setup")
    async def reaction(self, ctx):
        embed = discord.Embed(title="Reaction", color=discord.Color.random(), description="Create reaction roles")
        command = self.bot.get_command("reaction")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"reaction {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @reaction.command(help="Set up reaction role")
    @commands.has_permissions(manage_messages=True)
    async def create(self, ctx):
        await ctx.send("Answer These Question In Next 10Min!")

        questions = ["Enter Message: ", "Enter Emojis: ", "Enter Roles (id): ", "Enter Channel: "]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)

            try:
                msg = await self.bot.wait_for('message', timeout=600.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Type Faster Next Time!")
                return
            else:
                answers.append(msg.content)

        emojis = answers[1].split(" ")
        roles = answers[2].split(" ")
        c_id = int(answers[3][2:-1])
        channel = self.bot.get_channel(c_id)

        bot_msg = await channel.send(answers[0])

        insert = {"id": bot_msg.id, "emojis": emojis, "roles": roles}
        await rcursor.insert_one(insert)
        for emoji in emojis:
            await bot_msg.add_reaction(emoji)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Global chat setup")
    async def gc(self, ctx):
        embed = discord.Embed(title="Global Chat", color=discord.Color.random(), description="Create reaction roles")
        command = self.bot.get_command("gc")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"gc {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @gc.command(help="Set global chat channel")
    @commands.has_permissions(manage_channels=True)
    async def set(self, ctx, channel: discord.TextChannel):
        result = await gcursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await gcursor.insert_one({"guild": ctx.guild.id, "channel": channel.id})
            await ctx.send(f"Global chat channel set to {channel.mention}")
        elif result is not None:
            await gcursor.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Global chat channel updated to {channel.mention}")

    @gc.command(help="Remove your server from global chat")
    @commands.has_permissions(manage_channels=True)
    async def remove(self, ctx):
        result = await gcursor.find_one({"guild": ctx.guild.id})
        if result is not None:
            await gcursor.delete_one(result)
            await ctx.send("Your server has been remove from global chat")
        else:
            await ctx.send("You don't have a global chat system")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Starboard stuff", aliases=['sb', 'star'])
    async def starboard(self, ctx):
        embed = discord.Embed(title="Starboard", color=discord.Color.random(), description="Create reaction roles")
        command = self.bot.get_command("starboard")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"starboard|sb|star {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @starboard.command(help="Show starboard stats")
    async def stats(self, ctx):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        embed = discord.Embed(title="Starboard Stats", color=discord.Color.random())
        embed.add_field(name="Starboard Channel", value=f"{self.bot.get_channel(result['channel']).mention}")
        embed.add_field(name="Starboard Emojis", value=f"{result['emojis']}")
        embed.add_field(name="Starboard Threshold", value=f"{result['threshold']} seconds")
        embed.add_field(name="Starboard Message Expire", value=f"{result['age']}")
        await ctx.send(embed=embed)

    @starboard.command(help="Setup starboard channel")
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await scursor.insert_one({"guild": ctx.guild.id, "channel": channel.id, "emoji": "⭐", "threshold": 2, "age": 3600 * 24})
            await ctx.send(f"Starboard channel set to {channel.mention}")
            return
        await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
        await ctx.send(f"Starboard channel updated to {channel.mention}")

    @starboard.command(help="Set starboard emoji amount", aliases=["amount"])
    @commands.has_permissions(manage_messages=True)
    async def threshold(self, ctx, threshold: int):
        if await scursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"threshold": threshold}})
        await ctx.send(f"Starboard threshold updated to {threshold}")

    @starboard.command(help="Disable starboard system")
    @commands.has_permissions(manage_channels=True)
    async def disable(self, ctx):
        if await scursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await scursor.delete_one({"guild": ctx.guild.id})
        await ctx.send("Starboard system disabled")