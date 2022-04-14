import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])

welcome_cursors = cluster["welcome"]["channel"]

pcursor = cluster["custom_prefix"]["prefix"]

rcursor = cluster["react_role"]['reaction_roles']

gcursor = cluster['bot']['gc']

scursor = cluster['sb']['config']


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


def check_value(v, *dtype):
    if v.lower() == 'false':
        return None
    if dtype == "int":
        return int(v)
    return v


def check_return_dtype(v):
    if v.lower() == 'false':
        return None
    return True


class Configuration(commands.Cog):
    emoji = "⚙️"

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Welcome system setup")
    async def welcome(self, ctx):
        await ctx.send_help(ctx.command)

    @welcome.command(name="wizard", help="Use wizard if you want to save time")
    @commands.has_permissions(manage_guild=True)
    async def welcome_wizard(self, ctx):
        if await welcome_cursors.find_one({"guild": ctx.guild.id}):
            await welcome_cursors.delete_one({"guild": ctx.guild.id})
        questions = [
            """
What do you want your welcome message:

Valid Variables:
```
{mention}: Mention the joined user
{username}: user name and discriminator
{count}: Display the member count
{name}: The user's name
{server}: The server's name   
```     
            """,
            """
What do you want your welcome dm will be:

Valid Variables:
```
{mention}: Mention the joined user
{username}: user name and discriminator
{count}: Display the member count
{name}: The user's name
{server}: The server's name 
```     
            """,
            "What role will i add when user join: (type `false` if you do not want one)",
            "What background link you want me to use: (type `false` if you want the default one)",
            "Last question, which channel you want to send the welcome message at:"
        ]
        answers = []
        msg = await ctx.send("Starting wizard")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await msg.edit(content=question)
            msg = await self.bot.wait_for('message', check=check)
            answers.append(msg.content)
            await ctx.channel.purge(limit=1)

        try:
            c_id = int(answers[4][2:-1])
        except ValueError:
            await msg.edit(
                content=f'Wizard crash because you failed to mention the channel correctly.  Please do it like this: {ctx.channel.mention}')
            return

        wrole = answers[2][2:-1]
        if wrole.lower() == 'false':
            wrole = 0
        wrole = int(wrole)

        await welcome_cursors.insert_one({
            "guild": ctx.guild.id,
            "channel": c_id,
            "message": answers[0],
            "dm": answers[1],
            "img": check_value(answers[3]) or "https://cdn.discordapp.com/attachments/875886792035946496/936446668293935204/bridge.png",
            "role": wrole
        })
        await msg.edit(content="Wizard complete!")

    @welcome.command(name="welcome", help="Setup welcome channel")
    @commands.has_permissions(manage_channels=True)
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}",
                      "dm": f"Have fun at **{ctx.guild.name}**",
                      "img": "https://cdn.discordapp.com/attachments/875886792035946496/936446668293935204/bridge.png",
                      "role": 0}
            await welcome_cursors.insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        else:
            await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @welcome.command(help="Remove welcome system", aliases=['disable'], name="remove")
    @commands.has_permissions(manage_channels=True)
    async def wremove(self, ctx):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a welcome system")
        await welcome_cursors.delete_one(result)
        await ctx.send("Welcome system has been remove")

    @welcome.command(help="Create your welcome message. Use welcome text var to see the list of variables", name="text")
    @commands.has_permissions(manage_messages=True)
    async def wtext(self, ctx, *, text):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
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

    @welcome.command(help="Setup welcome dm. Use welcome dm var to see the list of variables", name="dm")
    @commands.has_permissions(manage_messages=True)
    async def wdm(self, ctx, *, text):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        if text.lower() == "var":
            return await ctx.send("""
{mention}: Mention the joined user
{username}: user name and discriminator
{count}: Display the member count
{name}: The user's name
{server}: The server's name
                            """)
        await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
        await ctx.send(f"Welcome dm updated to ```{text}```")

    @welcome.command(help="Add role when member join", name="role")
    @commands.has_permissions(manage_roles=True)
    async def wrole(self, ctx, role: discord.Role):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"role": role.id}})
        await ctx.send(f"Successfully updated welcome role")

    @welcome.command(help="remove the give role when join system", name="roleremove")
    @commands.has_permissions(manage_roles=True)
    async def wroleremove(self, ctx):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"role": 0}})
        await ctx.send(f"Successfully remove welcome role")

    @welcome.command(help="Custom image. Make sure it's a link", aliases=["img"], name="image")
    @commands.has_permissions(manage_messages=True)
    async def wimage(self, ctx, *, link: str):
        result = await welcome_cursors.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        await welcome_cursors.update_one({"guild": ctx.guild.id}, {"$set": {"img": link}})
        await ctx.send(f"Successfully updated welcome image")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Custom prefix setup")
    async def prefix(self, ctx):
        await ctx.send_help(ctx.command)

    @prefix.command(help="Set custom prefix", name="set")
    @commands.has_permissions(manage_guild=True)
    async def pset(self, ctx, *, prefixes):
        result = await pcursor.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "prefix": f"{prefixes}"}
            await pcursor.insert_one(insert)
            await ctx.send(f"Server prefix set to `{prefixes}`")
        else:
            await pcursor.update_one({"guild": ctx.guild.id}, {"$set": {"prefix": f"{prefixes}"}})
            await ctx.send(f"Server prefix update to `{prefixes}`")

    @prefix.command(help="Set prefix back to default", name="remove")
    @commands.has_permissions(manage_guild=True)
    async def premove(self, ctx):
        result = await pcursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a custom prefix yet")
        await pcursor.delete_one(result)
        await ctx.send(f"Server prefix set back to default")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await pcursor.find_one({"guild": guild.id})
        if result is not None:
            await pcursor.delete_one({"guild": guild.id})

    @commands.command(help="Create a reaction role message")
    @commands.has_permissions(manage_roles=True)
    async def reaction(self, ctx):
        questions = ["Enter Message: ", "Enter Emojis: ", "Enter Roles (only type role id): ", "Enter Channel: "]
        answers = []
        msg = await ctx.send("Reaction role wizard")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await msg.edit(content=question)
            msg = await self.bot.wait_for('message', check=check)
            answers.append(msg.content)
            await ctx.channel.purge(limit=1)

        emojis = answers[1].split(" ")
        roles = answers[2].split(" ")
        c_id = int(answers[3][2:-1])
        channel = self.bot.get_channel(c_id)

        bot_msg = await channel.send(answers[0])

        insert = {"id": bot_msg.id, "emojis": emojis, "roles": roles, "guild": ctx.guild.id}
        await rcursor.insert_one(insert)
        for emoji in emojis:
            await bot_msg.add_reaction(emoji)
        await msg.edit(content="Wizard Complete. Now check the reaction role message")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Starboard stuff", aliases=['sb', 'star'])
    async def starboard(self, ctx):
        await ctx.send_help(ctx.command)

    @starboard.command(name="wizard", help="Use wizard if you want to save time")
    @commands.has_permissions(manage_guild=True)
    async def starboard_wizard(self, ctx):
        if await scursor.find_one({"guild": ctx.guild.id}):
            await scursor.delete_one({"guild": ctx.guild.id})
        embed = discord.Embed(title="Starboard Wizard", description="Use this wizard to setup starboard", color=self.bot.embed_color)
        msg = await ctx.send(embed=embed)
        questions = [
            "What should be the starboard emoji (type `false` if you want default ⭐️):",
            "What should be the starboard amount (type `false` if you want default value, which is 2):",
            "Do you want users to self star their own message (type `true` or `false`):",
            "Do you want users to star message inn NSFW channel (type `true` or `false`):",
            "Last question, which channel you want to send the starboard message at:"
        ]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            embed.description = question
            await msg.edit(embed=embed)
            msg_check = await self.bot.wait_for('message', check=check)
            answers.append(msg_check.content)
            await ctx.channel.purge(limit=1)

        try:
            c_id = int(answers[4][2:-1])
        except ValueError:
            await msg.edit(
                content=f'Wizard crash because you failed to mention the channel correctly.  Please do it like this: {ctx.channel.mention}')
            return

        insert_data = {
            "guild": ctx.guild.id,
            "channel": c_id,
            "emoji": check_value(answers[0]) or '⭐️',
            "threshold": check_value(answers[1], "int") or 2,
            "ignoreChannel": [],
            "lock": False,
            "selfStar": check_return_dtype(answers[2]) or False,
            "nsfw": check_return_dtype(answers[3]) or False
        }
        await scursor.insert_one(insert_data)
        embed.description = "Wizard finished successfully!"
        embed.add_field(name="Starboard Channel", value=self.bot.get_channel(c_id).mention)
        embed.add_field(name="Starboard Emoji", value=insert_data["emoji"])
        embed.add_field(name="Starboard Amount", value=insert_data["threshold"])
        embed.add_field(name="Self Star", value=insert_data["selfStar"])
        embed.add_field(name="Allow NSFW", value=insert_data["nsfw"])
        await msg.edit(embed=embed)

    @starboard.command(help="Show starboard stats", name="stats")
    async def sbstats(self, ctx):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        embed = discord.Embed(title="Starboard Stats", color=discord.Color.random())
        embed.add_field(name="Starboard Channel", value=f"{self.bot.get_channel(result['channel']).mention}")
        embed.add_field(name="Starboard Emoji", value=f"{result['emoji']}")
        embed.add_field(name="Starboard Amount", value=f"{result['threshold']}")
        embed.add_field(name="Starboard Ignored Channels",
                        value=f"{[self.bot.get_channel(channel).mention for channel in result['ignoreChannel']]}")
        await ctx.send(embed=embed)

    @starboard.command(name="channel", help="Setup starboard channel")
    @commands.has_permissions(manage_channels=True)
    async def starboard_channel(self, ctx, channel: discord.TextChannel):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await scursor.insert_one({
                "guild": ctx.guild.id,
                "channel": channel.id,
                "emoji": "⭐",
                "threshold": 2,
                "ignoreChannel": [],
                "lock": False,
                "selfStar": False,
                "nsfw": False
            })
            await ctx.send(f"Starboard channel set to {channel.mention}")
            return
        await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
        await ctx.send(f"Starboard channel updated to {channel.mention}")

    @starboard.command(help="Toggle self star", name="selfStar")
    @commands.has_permissions(manage_guild=True)
    async def sbselfStar(self, ctx):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if result['selfStar'] is True:
            await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"selfStar": False}})
            await ctx.send("Selfstar is now off")
        else:
            await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"selfStar": True}})
            await ctx.send("Selfstar is now on")

    @starboard.command(help="Ignore channels from starboard", name="ignoreChannel")
    @commands.has_permissions(manage_channels=True)
    async def sbignoreChannel(self, ctx, channel: discord.TextChannel):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if channel.id in result['ignoreChannel']:
            return await ctx.send("This channel is already ignored")
        await scursor.update_one({"guild": ctx.guild.id}, {"$push": {"ignoreChannel": channel.id}})
        await ctx.send(f"Ignored channels {[x.mention for x in channel]}")

    @starboard.command(help="Un ignore channels from starboard", name="unignoreChannel")
    @commands.has_permissions(manage_channels=True)
    async def sbunignoreChannel(self, ctx, channel: discord.TextChannel):
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if channel.id not in result['ignoreChannel']:
            return await ctx.send(f"{channel.mention} is not ignored")
        await scursor.update_one({"guild": ctx.guild.id}, {"$pull": {"ignoreChannel": channel.id}})
        await ctx.send(f"Unignored channels {[x.mention for x in channel]}")

    @starboard.command(help="Set starboard emoji amount", aliases=["threshold"], name="amounnt")
    @commands.has_permissions(manage_guild=True)
    async def sbamount(self, ctx, threshold: int):
        if await scursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"threshold": threshold}})
        await ctx.send(f"Starboard threshold updated to {threshold}")

    @starboard.command(help="Lock starboard to prevent spam", name="lock")
    @commands.has_permissions(manage_guild=True)
    async def sblock(self, ctx, value="true"):
        if value.lower() not in ['true', 'false']:
            return await ctx.send("Value should be `true` or `false`")
        if await scursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        if value.lower() == "true":
            if (await scursor.find_one({"guild": ctx.guild.id}))['lock'] is True:
                return await ctx.send("Starboard is already locked")
            await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"lock": True}})
            await ctx.send("Starboard is now LOCKED")
        elif value.lower() == "false":
            if (await scursor.find_one({"guild": ctx.guild.id}))['lock'] is False:
                return await ctx.send("Starboard is already unlocked")
            await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"lock": False}})
            await ctx.send("Starboard is now UNLOCKED")

    @starboard.command(help="Allow to star in nsfw channels. value should be yes or no", name="nsfw")
    @commands.has_permissions(manage_guild=True)
    async def sbnsfw(self, ctx, value="true"):
        if value.lower() not in ['true', 'false']:
            return await ctx.send("Value should be `true` or `false`")
        result = await scursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if value.lower() == "true":
            if result['nsfw'] is True:
                return await ctx.send("NSFW is already allowed")
            await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"nsfw": True}})
            await ctx.send("NSFW is now allowed")
        elif value.lower() == "false":
            if result['nsfw'] is False:
                return await ctx.send("NSFW is already not allowed")
            await scursor.update_one({"guild": ctx.guild.id}, {"$set": {"nsfw": False}})
            await ctx.send("NSFW is now false")

    @starboard.command(help="Disable starboard system", name="ignoreChannel")
    @commands.has_permissions(manage_guild=True)
    async def sbdisable(self, ctx):
        if await scursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await scursor.delete_one({"guild": ctx.guild.id})
        await ctx.send("Starboard system disabled")
