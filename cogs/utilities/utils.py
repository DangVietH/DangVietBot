import discord
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
from utils import config_var
import datetime
from utils import DefaultPageSource, MenuPages

cluster = AsyncIOMotorClient(config_var["mango_link"])
timer = cluster["timer"]['remind']
afk = cluster["timer"]['afk']
tagCursor = cluster["bot"]["tag"]


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


class Utils(commands.Cog):
    emoji = "📝"

    def __init__(self, bot):
        self.bot = bot
        self.time_checker.start()

    @commands.group(help="Remind your task", invoke_without_command=True, case_insensitive=True)
    async def remind(self, ctx, time, *, reason):
        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")

        if converted_time == -2:
            return await ctx.send("Time must be an integer")
        current_time = datetime.datetime.now()
        final_time = current_time + datetime.timedelta(seconds=converted_time)
        await timer.insert_one({"id": ctx.message.id, "user": ctx.author.id, "time": final_time, "reason": reason})
        await ctx.send("⏰ Reminder set")

    @remind.command(name="delete", help="Delete an unwanted reminder")
    async def remind_delete(self, ctx, remind_id: int):
        if await timer.find_one({"id": remind_id}) is None:
            return await ctx.send("You don't have that reminder")
        await timer.delete_one({"id": remind_id})
        await ctx.send("Reminder deleted!")

    @remind.command(name="list", help="See your remind list")
    async def remind_list(self, ctx):
        all_timer = timer.find({'user': ctx.author.id})
        if all_timer is None:
            return await ctx.send("You don't have any reminders")
        data = []
        async for x in all_timer:
            data.append((f"{x['id']}", f"**End at:** <t:{int(datetime.datetime.timestamp(x['time']))}:R> **Reason:** {x['reason']}"))
        page = MenuPages(DefaultPageSource(f"Your reminder list", data), ctx)
        await page.start()

    @tasks.loop(seconds=10)
    async def time_checker(self):
        try:
            all_timer = timer.find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    user = self.bot.get_user(x['user'])
                    await user.send(f"**Reminder:** {x['reason']}")
                    await timer.delete_one({"user": user.id})
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if await afk.find_one({"guild": message.guild.id, "member": message.author.id}) is not None:
            await afk.delete_one({"guild": message.guild.id, "member": message.author.id})
            await message.channel.send(f"{message.author.mention}, I have remove your afk")
        if message.mentions:
            for mention in message.mentions:
                is_afk = await afk.find_one({"guild": message.guild.id, "member": mention.id})
                if is_afk is not None:
                    await message.channel.send(f"`{mention}` is currently afk! Reason: **{is_afk['reason']}**")

    @commands.command(help="Tell people that ur gone")
    async def afk(self, ctx, *, reason="Poop"):
        if await afk.find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is not None:
            return await ctx.send("You're already afk")
        await afk.insert_one({"guild": ctx.guild.id, "member": ctx.author.id, "reason": reason})
        await ctx.send(f"You're now afk for: **{reason}**")

    @commands.command(aliases=['math'], help="Do math stuff")
    async def calculate(self, ctx, num1: float, op: str, num2: float):
        if op == "+":
            await ctx.send(num1 + num2)
        elif op == "-":
            await ctx.send(num1 - num2)
        elif op == "*":
            await ctx.send(num1 * num2)
        elif op == "/":
            await ctx.send(num1 / num2)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Tag setup")
    async def tag(self, ctx, *, name=None):
        if name is None:
            return await ctx.send_help(ctx.command)

        all_tag = (await tagCursor.find_one({"guild": ctx.guild.id}))['tag']
        value = None
        for thing in all_tag:
            if thing['name'] == name:
                value = thing['value']
                break
        if value is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

        await ctx.send(value)

    @tag.command(help="Create a tag", name="create")
    async def tagcreate(self, ctx):
        questions = ["What is the tag name: ",
                     "What is the tag value: "]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)
            msg = await self.bot.wait_for('message', check=check)
            answers.append(msg.content)
        check = await tagCursor.find_one({"guild": ctx.guild.id})
        if check is None:
            await tagCursor.insert_one({"guild": ctx.guild.id, "tag": [
                {"name": answers[0], "value": answers[1], "owner": ctx.author.id}
            ]})
            await ctx.send(f"Tag {answers[0]} successfully created")
        else:
            is_exist = await tagCursor.find_one({"guild": ctx.guild.id, "tag.name": answers[0]})
            if is_exist is not None:
                await ctx.send("Tag already exist. Remember that tag name are case SENSITIVE")
            else:
                await tagCursor.update_one({"guild": ctx.guild.id}, {
                    "$push": {"tag": {"name": answers[0], "value": answers[1], "owner": ctx.author.id}}})
                await ctx.send(f"Tag {answers[0]} successfully created")

    @tag.command(help="Remove a tag", aliases=['remove'], name="delete")
    @commands.has_permissions(manage_guild=True)
    async def tagdelete(self, ctx, *, name):
        if await tagCursor.find_one({"guild": ctx.guild.id, "tag.name": name}) is None:
            await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        else:
            await tagCursor.update_one({"guild": ctx.guild.id}, {"$pull": {"tag": {"name": name}}})
            await ctx.send("Tag deleted successfully")

    @tag.command(help="Edit a tag", name="edit")
    async def tagedit(self, ctx, *, name):
        gcheck = await tagCursor.find_one({"guild": ctx.guild.id})
        if gcheck is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

        tnname = None
        owner = None
        for thing in gcheck['tag']:
            if thing['name'] == name:
                tnname = thing['name']
                owner = thing['owner']
                break

        if tnname is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

        if ctx.author.id != owner:
            return await ctx.send("You are not the owner of this tag")
        await ctx.send("What is the new tag value: `Type end to abort the process`")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        user_choice = (await self.bot.wait_for('message', check=check)).content
        if user_choice == "end".lower():
            return await ctx.send("Task abort successfully")
        await tagCursor.update_one({"guild": ctx.guild.id, "tag.name": name}, {"$set": {"tag.value": user_choice}})
        await ctx.send("Tag edited successfully")

    @tag.command(help="See a list of tags", name="list")
    async def taglist(self, ctx):
        check = await tagCursor.find_one({"guild": ctx.guild.id})
        if check is None:
            return await ctx.send("No tags in here")
        data = []
        ta = check['tag']
        for thing in ta:
            to_append = (thing['name'], f"**Owner:** {self.bot.get_user(thing['owner'])}")
            data.append(to_append)
        page = MenuPages(DefaultPageSource(f"Tags of {ctx.guild.name}", data), ctx)
        await page.start()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        check = await tagCursor.find_one({"guild": guild.id})
        if check is not None:
            await tagCursor.delete_one({"guild": guild.id})

    @commands.command(help="Suggest something to this bot")
    async def suggest(self, ctx, *, text):
        channel = self.bot.get_channel(887949939676684338)
        embed = discord.Embed(title="Incoming Suggestion", description=f"We got a suggestion from {ctx.author.mention}", color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Text", value=f"```{text}```")
        embed.set_footer(text="To suggest something, do d!suggest <suggestion>")
        msg = await channel.send(embed=embed)
        await msg.add_reaction('🔼')
        await msg.add_reaction('🔽')
        await ctx.send("Message sent to the suggestion channel in our support server")

    @commands.command(help="Report a bug of the bot")
    async def bug(self, ctx, *, text):
        channel = self.bot.get_channel(921375785112195102)
        embed = discord.Embed(title="Incoming Report", description=f"We got a bug reported by {ctx.author.mention}",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Text", value=f"```{text}```")
        embed.set_footer(text="To report a bug, do d!bug <bug>")
        await channel.send(embed=embed)
        await ctx.send("Message sent to the bug channel in our support server")
