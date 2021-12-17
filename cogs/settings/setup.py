import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))

wdbs = cluster["welcome"]
welcome_cursors = wdbs["channel"]

pdb = cluster["custom_prefix"]
pcursor = pdb["prefix"]

rdb = cluster["react_role"]
rcursor = rdb['reaction_roles']

text_for_welcome = """```
welcome channel [channel] - Setup welcome channel
welcome remove - Remove welcome system
welcome text <text>  - Create your welcome message
welcome dm <text>  - Create your welcome dm
```"""

text_for_prefix = """```
prefix set <prefix> - set up custom prefix
prefix remove - set prefix back to default
```"""

text_for_reaction = """```
reaction create - create reaction roles
reaction delete [message_id] - Delete reaction role system of a message. Make sure your at the same channel as the message so I can delete it
```"""


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Welcome system setup")
    async def welcome(self, ctx):
        embed = discord.Embed(title="Welcome", color=discord.Color.random(), description="Set up welcome system")
        for command in self.bot.get_command("welcome").walk_commands():
            embed.add_field(name=f"{command}", value=f"{command.description}")
        await ctx.send(embed=embed)

    @welcome.command(help="Setup welcome channel")
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}",
                      "dm": f"Have fun at **{ctx.guild.name}**"}
            await welcome_cursors.insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        elif result is not None:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @welcome.command(help="Remove welcome system")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is not None:
            await welcome_cursors.delete_one(result)
            await ctx.send("Welcome system has been remove")
        else:
            await ctx.send("You don't have a welcome system")

    @welcome.command(help="Create your welcome message")
    @commands.has_permissions(administrator=True)
    async def text(self, ctx, *, text):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
            await ctx.send(f"Welcome message updated to ```{text}```")

    @welcome.command(help="Setup welcome dm")
    @commands.has_permissions(administrator=True)
    async def dm(self, ctx, *, text):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You haven't configure a welcome channel yet")
        else:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
            await ctx.send(f"Welcome dm updated to ```{text}```")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Custom prefix setup")
    async def prefix(self, ctx):
        embed = discord.Embed(title="Prefix", color=discord.Color.random(), description="Set up custom prefix")
        for command in self.bot.get_command("prefix").walk_commands():
            embed.add_field(name=f"{command}", value=f"{command.description}")
        await ctx.send(embed=embed)

    @prefix.command(help="Set custom prefix")
    @commands.has_permissions(administrator=True)
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
    @commands.has_permissions(administrator=True)
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
        for command in self.bot.get_command("reaction").walk_commands():
            embed.add_field(name=f"{command}", value=f"{command.description}")
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

    @reaction.command(help="Delete reaction role system")
    @commands.has_permissions(manage_messages=True)
    async def delete(self, ctx, msg_id: int):
        check = await rcursor.find_one({"id": msg_id})
        if msg_id == check['id']:
            msg = await ctx.fetch_message(msg_id)
            await msg.delete()
            await rcursor.delete_one(check)
            await ctx.send("Mission complete")
        else:
            await ctx.send("Can't find that message id")