import discord
from discord.ext import commands
from utils import SecondPageSource, MenuPages


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


def has_automod():
    async def predicate(ctx):
        data = await ctx.bot.mongo["moderation"]['automod'].find_one({"guild": ctx.guild.id})
        if data is None:
            await ctx.send(f"This server has no automod settings. Please use `{ctx.prefix}automod set` to set them.")
            return False
        return True

    return commands.check(predicate)


def has_config_role():
    """Anyone with the config role can use the config commands."""

    async def predicate(ctx):
        result = await ctx.bot.mongo["bot"]['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            return False
        if ctx.guild.get_role(result['role']) in ctx.author.roles:
            return True

    return commands.check(predicate)


class Configuration(commands.Cog):
    emoji = "⚙️"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Anyone with this role can use the commands in the Configuration category")
    @commands.has_permissions(manage_roles=True)
    async def configrole(self, ctx, role: discord.Role):
        data = await self.bot.mongo["bot"]['config'].find_one({"guild": ctx.guild.id})
        if data is None:
            await self.bot.mongo["bot"]['config'].insert_one({"guild": ctx.guild.id, "role": role.id})
        else:
            await self.bot.mongo["bot"]['config'].update_one({"guild": ctx.guild.id},
                                                             {"$set": {"role": role.id}})
        await ctx.send(
            f"Config role set to **{role.name}**! Anyone with this role can use any command in the Configuration category (except custom prefix).")

    @commands.command(help="Set up modlog channel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    @commands.bot_has_permissions(manage_channels=True, view_audit_log=True)
    async def modlog(self, ctx, channel: discord.TextChannel):
        result = await self.bot.mongo["moderation"]['modlog'].find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await self.bot.mongo["moderation"]['modlog'].insert_one(insert)
            await ctx.send(f"Modlog channel set to {channel.mention}")
            return
        await self.bot.mongo["moderation"]['modlog'].update_one({"guild": ctx.guild.id},
                                                                {"$set": {"channel": channel.id}})
        await ctx.send(f"Modlog channel updated to {channel.mention}")

    @commands.command(help="Set up custom mod role")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    @commands.bot_has_permissions(manage_roles=True)
    async def modrole(self, ctx, role: discord.Role):
        result = await self.bot.mongo["moderation"]['modrole'].find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "role": role.id}
            await self.bot.mongo["moderation"]['modrole'].insert_one(insert)
            await ctx.send(f"Mod role set to {role.name}")
            return
        await self.bot.mongo["moderation"]['modrole'].update_one({"guild": ctx.guild.id}, {"$set": {"role": role.id}})
        await ctx.send(f"Mod role updated to {role.name}")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Welcome system setup")
    async def welcome(self, ctx):
        await ctx.send_help(ctx.command)

    @welcome.command(name="wizard", help="Use wizard if you want to save time")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def welcome_wizard(self, ctx):
        if await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id}):
            await self.bot.mongo["welcome"]["channel"].delete_one({"guild": ctx.guild.id})
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
            "What background link you want me to use: (type `false` if you want the default one)",
            "Last question, which channel you want to send the welcome message at:"
        ]
        answers = []
        msg = await ctx.send("Starting wizard")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await msg.edit(content=question)
            user_msg = await self.bot.wait_for('message', check=check)
            answers.append(user_msg.content)
            await ctx.channel.purge(limit=1)

        try:
            c_id = int(answers[3][2:-1])
        except ValueError:
            await msg.edit(
                content=f'Wizard crash because you failed to mention the channel correctly.  Please do it like this: {ctx.channel.mention}')
            return

        await self.bot.mongo["welcome"]["channel"].insert_one({
            "guild": ctx.guild.id,
            "channel": c_id,
            "message": answers[0],
            "dm": answers[1],
            "img": check_value(answers[
                                   2]) or "https://cdn.discordapp.com/attachments/875886792035946496/936446668293935204/bridge.png",
            "role": 0
        })
        await msg.edit(content="Wizard complete!")

    @welcome.command(name="welcome", help="Setup welcome channel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id, "message": "Welcome {mention}",
                      "dm": f"Have fun at **{ctx.guild.name}**",
                      "img": "https://cdn.discordapp.com/attachments/875886792035946496/936446668293935204/bridge.png",
                      "role": 0}
            await self.bot.mongo["welcome"]["channel"].insert_one(insert)
            await ctx.send(f"Welcome channel set to {channel.mention}")
        else:
            await self.bot.mongo["welcome"]["channel"].update_one({"guild": ctx.guild.id},
                                                                  {"$set": {"channel": channel.id}})
            await ctx.send(f"Welcome channel updated to {channel.mention}")

    @welcome.command(help="Disable welcome system", name="disable")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def wdisable(self, ctx):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a welcome system")
        await self.bot.mongo["welcome"]["channel"].delete_one(result)
        await ctx.send("Welcome system has been remove")

    @welcome.command(help="Create your welcome message. Use welcome text var to see the list of variables", name="text")
    @commands.check_any(commands.has_permissions(manage_messages=True), has_config_role())
    async def wtext(self, ctx, *, text):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
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
        await self.bot.mongo["welcome"]["channel"].update_one({"guild": ctx.guild.id}, {"$set": {"message": text}})
        await ctx.send(f"Welcome message updated to ```{text}```")

    @welcome.command(help="Setup welcome dm. Use welcome dm var to see the list of variables", name="dm")
    @commands.check_any(commands.has_permissions(manage_messages=True), has_config_role())
    async def wdm(self, ctx, *, text):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
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
        await self.bot.mongo["welcome"]["channel"].update_one({"guild": ctx.guild.id}, {"$set": {"dm": text}})
        await ctx.send(f"Welcome dm updated to ```{text}```")

    @welcome.command(help="Add role when member join", name="role")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def wrole(self, ctx, role: discord.Role):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        await self.bot.mongo["welcome"]["channel"].update_one({"guild": ctx.guild.id}, {"$set": {"role": role.id}})
        await ctx.send(f"Successfully updated welcome role")

    @welcome.command(help="remove the give role when join system", name="roleremove")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def wroleremove(self, ctx):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        await self.bot.mongo["welcome"]["channel"].update_one({"guild": ctx.guild.id}, {"$set": {"role": 0}})
        await ctx.send(f"Successfully remove welcome role")

    @welcome.command(help="Custom image. Make sure it's a link", aliases=["img"], name="image")
    @commands.check_any(commands.has_permissions(manage_messages=True), has_config_role())
    async def wimage(self, ctx, *, link: str):
        result = await self.bot.mongo["welcome"]["channel"].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You haven't configure a welcome channel yet")
        await self.bot.mongo["welcome"]["channel"].update_one({"guild": ctx.guild.id}, {"$set": {"img": link}})
        await ctx.send(f"Successfully updated welcome image")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Custom prefix setup")
    async def prefix(self, ctx):
        await ctx.send_help(ctx.command)

    @prefix.command(help="Set custom prefix", name="set")
    @commands.has_permissions(manage_guild=True)
    async def pset(self, ctx, *, prefixes):
        result = await self.bot.mongo["custom_prefix"]["prefix"].find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "prefix": f"{prefixes}"}
            await self.bot.mongo["custom_prefix"]["prefix"].insert_one(insert)
            await ctx.send(f"Server prefix set to `{prefixes}`")
        else:
            await self.bot.mongo["custom_prefix"]["prefix"].update_one({"guild": ctx.guild.id},
                                                                       {"$set": {"prefix": f"{prefixes}"}})
            await ctx.send(f"Server prefix update to `{prefixes}`")

    @prefix.command(help="Set prefix back to default", name="remove")
    @commands.has_permissions(manage_guild=True)
    async def premove(self, ctx):
        result = await self.bot.mongo["custom_prefix"]["prefix"].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a custom prefix yet")
        await self.bot.mongo["custom_prefix"]["prefix"].delete_one(result)
        await ctx.send(f"Server prefix set back to default")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await self.bot.mongo["custom_prefix"]["prefix"].find_one({"guild": guild.id})
        if result is not None:
            await self.bot.mongo["custom_prefix"]["prefix"].delete_one({"guild": guild.id})

    @commands.command(help="Create a reaction role message")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def reaction(self, ctx):
        questions = [
            "Hello. What will be your reaction role message? ",
            "Alright, now we will add the emojis\n **NOTE: We do not support custom emojis right now.**",
            "Nice, now we will add the roles\nMake sure you mention the role and add space between them. You also put the roles in the same order as the emojis.**",
            "Finally, Enter the Channel you want the message to be in?: "
        ]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)
            user_msg = await self.bot.wait_for('message', check=check)
            answers.append(user_msg.content)

        emojis = answers[1].split(" ")
        roles = answers[2].split(" ")
        c_id = int(answers[3][2:-1])
        channel = self.bot.get_channel(c_id)

        for r in range(len(roles)):
            roles[r] = int(roles[r][3:-1])

        bot_msg = await channel.send(answers[0])

        insert = {"id": bot_msg.id, "emojis": emojis, "roles": roles, "guild": ctx.guild.id}
        await self.bot.mongo["react_role"]['reaction_roles'].insert_one(insert)
        for emoji in emojis:
            await bot_msg.add_reaction(emoji)
        await ctx.send("Wizard Complete. Now check the reaction role message")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Starboard stuff", aliases=['sb', 'star'])
    async def starboard(self, ctx):
        await ctx.send_help(ctx.command)

    @starboard.command(name="wizard", help="Use wizard if you want to save time")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def starboard_wizard(self, ctx):
        if await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id}):
            await self.bot.mongo['sb']['config'].delete_one({"guild": ctx.guild.id})
        embed = discord.Embed(title="Starboard Wizard", description="Use this wizard to setup starboard",
                              color=self.bot.embed_color)
        msg = await ctx.send(embed=embed)
        questions = [
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
            c_id = int(answers[3][2:-1])
        except ValueError:
            await msg.edit(
                content=f'Wizard crash because you failed to mention the channel correctly.  Please do it like this: {ctx.channel.mention}')
            return

        insert_data = {
            "guild": ctx.guild.id,
            "channel": c_id,
            "emoji": '⭐️',
            "threshold": check_value(answers[0], "int") or 2,
            "ignoreChannel": [],
            "lock": False,
            "selfStar": check_return_dtype(answers[1]) or False,
            "nsfw": check_return_dtype(answers[2]) or False
        }
        await self.bot.mongo['sb']['config'].insert_one(insert_data)
        embed.description = "Wizard finished successfully!"
        embed.add_field(name="Starboard Channel", value=self.bot.get_channel(c_id).mention)
        embed.add_field(name="Starboard Emoji", value=insert_data["emoji"])
        embed.add_field(name="Starboard Amount", value=insert_data["threshold"])
        embed.add_field(name="Self Star", value=insert_data["selfStar"])
        embed.add_field(name="Allow NSFW", value=insert_data["nsfw"])
        await msg.edit(embed=embed)

    @starboard.command(help="Show starboard stats", name="stats")
    async def sbstats(self, ctx):
        result = await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        embed = discord.Embed(title="Starboard Stats", color=discord.Color.random())
        embed.add_field(name="Channel", value=f"{self.bot.get_channel(result['channel']).mention}")
        embed.add_field(name="Is Lock", value=f"{result['lock']}")
        embed.add_field(name="Emoji", value=f"{result['emoji']}")
        embed.add_field(name="Amount", value=f"{result['threshold']}")
        embed.add_field(name="Allow NSFW", value=f"{result['nsfw']}")
        embed.add_field(name="Allow Self Star", value=f"{result['selfStar']}")
        embed.add_field(name="Ignored Channels",
                        value=f"{[self.bot.get_channel(channel).mention for channel in result['ignoreChannel']]}")
        await ctx.send(embed=embed)

    @starboard.command(name="channel", help="Setup starboard channel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def starboard_channel(self, ctx, channel: discord.TextChannel):
        result = await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            await self.bot.mongo['sb']['config'].insert_one({
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
        await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
        await ctx.send(f"Starboard channel updated to {channel.mention}")

    @starboard.command(help="Toggle self star", name="selfStar")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def sbselfStar(self, ctx):
        result = await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if result['selfStar'] is True:
            await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"selfStar": False}})
            await ctx.send("Selfstar is now off")
        else:
            await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"selfStar": True}})
            await ctx.send("Selfstar is now on")

    @starboard.command(help="Ignore channels from starboard", name="ignoreChannel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def sbignoreChannel(self, ctx, channel: discord.TextChannel):
        result = await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if channel.id in result['ignoreChannel']:
            return await ctx.send("This channel is already ignored")
        await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id},
                                                        {"$addToSet": {"ignoreChannel": channel.id}})
        await ctx.send(f"Ignored channels {[x.mention for x in channel]}")

    @starboard.command(help="Un ignore channels from starboard", name="unignoreChannel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def sbunignoreChannel(self, ctx, channel: discord.TextChannel):
        result = await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if channel.id not in result['ignoreChannel']:
            return await ctx.send(f"{channel.mention} is not ignored")
        await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id},
                                                        {"$pull": {"ignoreChannel": channel.id}})
        await ctx.send(f"Unignored channels {[x.mention for x in channel]}")

    @starboard.command(help="Set starboard emoji amount", aliases=["threshold"], name="amounnt")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def sbamount(self, ctx, threshold: int):
        if await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"threshold": threshold}})
        await ctx.send(f"Starboard threshold updated to {threshold}")

    @starboard.command(help="Lock starboard to prevent spam", name="lock")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def sblock(self, ctx, value="true"):
        if value.lower() not in ['true', 'false']:
            return await ctx.send("Value should be `true` or `false`")
        if await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        if value.lower() == "true":
            if (await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id}))['lock'] is True:
                return await ctx.send("Starboard is already locked")
            await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"lock": True}})
            await ctx.send("Starboard is now LOCKED")
        elif value.lower() == "false":
            if (await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id}))['lock'] is False:
                return await ctx.send("Starboard is already unlocked")
            await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"lock": False}})
            await ctx.send("Starboard is now UNLOCKED")

    @starboard.command(help="Allow to star in nsfw channels. value should be yes or no", name="nsfw")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def sbnsfw(self, ctx, value="true"):
        if value.lower() not in ['true', 'false']:
            return await ctx.send("Value should be `true` or `false`")
        result = await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if value.lower() == "true":
            if result['nsfw'] is True:
                return await ctx.send("NSFW is already allowed")
            await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"nsfw": True}})
            await ctx.send("NSFW is now allowed")
        elif value.lower() == "false":
            if result['nsfw'] is False:
                return await ctx.send("NSFW is already not allowed")
            await self.bot.mongo['sb']['config'].update_one({"guild": ctx.guild.id}, {"$set": {"nsfw": False}})
            await ctx.send("NSFW is now false")

    @starboard.command(help="Disable starboard system", name="disable")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def sbdisable(self, ctx):
        if await self.bot.mongo['sb']['config'].find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await self.bot.mongo['sb']['config'].delete_one({"guild": ctx.guild.id})
        await ctx.send("Starboard system disabled")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Economy Configuration")
    async def econfig(self, ctx):
        await ctx.send_help(ctx.command)

    @econfig.command(help="Set the currency symbol", name="symbol")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def econfig_symbol(self, ctx, symbol):
        if len(symbol) < 1:
            return await ctx.send("Symbol should only be 1 character")
        await self.bot.mongo["economy"]["server"].update_one({"guild": ctx.guild.id},
                                                             {"$set": {"econ_symbol": symbol}})
        await ctx.send("Economy symbol set to `{}`".format(symbol))

    @econfig.command(name="shop_add", help="Add item to the shop")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def econfig_shop_add(self, ctx, name: str, price: int):
        await self.bot.mongo["economy"]["server"].update_one({"guild": ctx.guild.id},
                                         {"$addToSet": {"shop": {"name": name, "price": price}}})
        await ctx.send(f"Added {name} to the shop!")

    @econfig.command(name="shop_remove", help="Remove an item from the shop")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def econfig_shop_remove(self, ctx, name: str):
        if await self.bot.mongo["economy"]["server"].find_one({"guild": ctx.guild.id, "shop.name": name}) is None:
            return await ctx.send("That item isn't in the shop!")
        await self.bot.mongo["economy"]["server"].update_one({"guild": ctx.guild.id}, {"$pull": {"shop": {"name": name}}})
        await ctx.send(f"Removed {name} from the shop!")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Level Configuration")
    async def lvl(self, ctx):
        await ctx.send_help(ctx.command)

    @lvl.command(help="Custom level up message. Use welcome text var to see the list of variables", name="text")
    @commands.check_any(commands.has_permissions(manage_messages=True), has_config_role())
    async def lvltext(self, ctx, *, text):
        if text.lower() == "var":
            return await ctx.send("""
{mention}: Mention the joined user
{username}: user name and discriminator
{name}: The user's name
{server}: The server's name
                            """)
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id}, {"$set": {"msg": text}})
        await ctx.send(f"Welcome message updated to ```{text}```")

    @lvl.group(invoke_without_command=True, case_insensitive=True, help="Level role configuration", name="role")
    async def lvlrole(self, ctx):
        await ctx.send_help(ctx.command)

    @lvlrole.command(help="Set up rewarding role system", name="add")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def lvlroleadd(self, ctx, level: int, roles: discord.Role):
        role_cursor = await self.bot.mongo["levelling"]['roles'].find_one({"guild": ctx.guild.id})
        if roles.id in role_cursor['role']:
            return await ctx.send("That role is already added")
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id},
                                                              {"$push": {"role": roles.id, "level": level}})
        await ctx.send(f"**{roles.name}** role set to level **{level}**")

    @lvlrole.command(help="Remove the role from level", name="remove")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def lvlroleremove(self, ctx, level: int, roles: discord.Role):
        role_cursor = await self.bot.mongo["levelling"]['roles'].find_one({"guild": ctx.guild.id})
        if roles.id not in role_cursor['role']:
            return await ctx.send("I don't remember I put that role in. Do role list to see all the roles")
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id},
                                                              {"$pull": {"role": roles.id, "level": level}})
        await ctx.send(f"{roles.name} role remove.")

    @lvlrole.command(help="See list of rewarding roles", name="list")
    async def lvlrolelist(self, ctx):
        role_cursor = await self.bot.mongo["levelling"]['roles'].find_one({"guild": ctx.guild.id})
        levelrole = role_cursor['role']
        levelnum = role_cursor['level']
        data = []
        for i in range(len(levelrole)):
            data.append((f"Level **{levelnum[i]}** role reward", ctx.guild.get_role(levelrole[i]).mention))
        page = MenuPages(source=SecondPageSource(f"{ctx.author.guild.name} role rewards", data),
                         ctx=ctx)
        await page.start()

    @lvl.command(help="Setup level up channel if you like to")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def setlevelchannel(self, ctx, channel: discord.TextChannel):
        result = await self.bot.mongo["levelling"]['channel'].find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await self.bot.mongo["levelling"]['channel'].insert_one(insert)
            await ctx.send(f"All level up message will be sent to {channel.mention}")
        elif result is not None:
            await self.bot.mongo["levelling"]['channel'].update_one({"guild": ctx.guild.id},
                                                                    {"$set": {"channel": channel.id}})
            await ctx.send(f"All level up message will be sent to {channel.mention}")

    @lvl.command(help="Remove level up message from that channel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def removelevelchannel(self, ctx):
        result = await self.bot.mongo["levelling"]['channel'].find_one({"guild": ctx.guild.id})
        if result is None:
            await ctx.send("You don't have a level up channel")
        else:
            await self.bot.mongo["levelling"]['channel'].delete_one(result)
            await ctx.send(f"All level up message will be sent after member message")

    @lvl.command(help="No add xp if member has this role",
                 name="ignorerole")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def lvlignorerole(self, ctx, role: discord.Role):
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id},
                                                              {"$addToSet": {"ignoreRole": role.id}})
        await ctx.send(f"Any member with {role.name} role will not receive level xp")

    @lvl.command(help="Ignore a channel for level system",
                 name="ignorechannel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def lvlignorechannel(self, ctx, channel: discord.TextChannel):
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id},
                                                              {"$addToSet": {"ignoreChannel": channel.id}})
        await ctx.send(f"Nobody can receive xp in {channel.mention}")

    @lvl.command(help="Unignored a role from the role ignore list",
                 name="unignorerole")
    @commands.check_any(commands.has_permissions(manage_roles=True), has_config_role())
    async def lvlunignorerole(self, ctx, role: discord.Role):
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id},
                                                              {"$pull": {"ignoreRole": role.id}})
        await ctx.message.add_reaction("✅")

    @lvl.command(help="Unignored a channel from the channel ignore list",
                 name="unignorechannel")
    @commands.check_any(commands.has_permissions(manage_channels=True), has_config_role())
    async def lvlunignorechannel(self, ctx, channel: discord.TextChannel):
        await self.bot.mongo["levelling"]['roles'].update_one({"guild": ctx.guild.id},
                                                              {"$pull": {"ignoreChannel": channel.id}})
        await ctx.message.add_reaction("✅")

    @lvl.command(help="Disable levelling", name="disable")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def lvldisable(self, ctx):
        check = await self.bot.mongo["levelling"]['disable'].find_one({"guild": ctx.guild.id})
        if check:
            return await ctx.send("Leveling already disabled")
        insert = {"guild": ctx.guild.id}
        await self.bot.mongo["levelling"]['disable'].insert_one(insert)
        for member in ctx.guild.members:
            if not member.bot:
                result = await self.bot.mongo["levelling"]['member'].find_one(
                    {"guild": ctx.guild.id, "user": member.id})
                if result is not None:
                    await self.bot.mongo["levelling"]['member'].delete_one({"guild": ctx.guild.id, "user": member.id})
        await self.bot.mongo["levelling"]['roles'].delete_one({"guild": ctx.guild.id})
        await ctx.send('Levelling disabled')

    @lvl.command(help="Re-enable levelling", name="enable")
    @commands.check_any(commands.has_permissions(manage_guild=True), has_config_role())
    async def lvlenable(self, ctx):
        check = await self.bot.mongo["levelling"]['disable'].find_one({"guild": ctx.guild.id})
        if check is None:
            return await ctx.send('Leveling already enabled')
        await self.bot.mongo["levelling"]['disable'].delete_one(check)
        await ctx.send('Levelling enabled')

        results = await self.bot.mongo["levelling"]['roles'].find_one({"guild": ctx.guild.id})
        if results is None:
            await self.bot.mongo["levelling"]['roles'].insert_one(
                {"guild": ctx.guild.id, "role": [], "level": [], "ignoreChannel": [], "ignoreRole": [], "xp": 10,
                 "msg": "🎉 {mention} has reached level **{level}**!!🎉"})
