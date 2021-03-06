import discord
from discord.ext import commands, tasks
import datetime
from utils import DefaultPageSource, MenuPages


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

    async def cog_unload(self):
        self.time_checker.cancel()

    @tasks.loop(seconds=5)
    async def time_checker(self):
        try:
            all_timer = self.bot.mongo["timer"]['remind'].find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    user = self.bot.get_user(x['user'])
                    await user.send(f"**Reminder:** {x['reason']}")
                    await self.bot.mongo["timer"]['remind'].delete_one(x)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if await self.bot.mongo["timer"]['afk'].find_one({"guild": message.guild.id, "member": message.author.id}):
            await self.bot.mongo["timer"]['afk'].delete_one({"guild": message.guild.id, "member": message.author.id})
            await message.channel.send(f"{message.author.mention}, I have remove your afk")
        if message.mentions:
            for mention in message.mentions:
                is_afk = await self.bot.mongo["timer"]['afk'].find_one({"guild": message.guild.id, "member": mention.id})
                if is_afk:
                    await message.channel.send(f"`{mention}` is currently afk! Reason: **{is_afk['reason']}**")

    @commands.command(help="Tell people that ur gone")
    async def afk(self, ctx, *, reason="Poop"):
        if await self.bot.mongo["timer"]['afk'].find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is not None:
            return await ctx.send("You're already afk")
        await self.bot.mongo["timer"]['afk'].insert_one(
            {"guild": ctx.guild.id, "member": ctx.author.id, "reason": reason})
        await ctx.send(f"You're now afk for: **{reason}**")

    @commands.group(help="Remind a task you want to complete", invoke_without_command=True, case_insensitive=True,
                    aliases=['reminder', 'remind', 'notify'])
    async def remindme(self, ctx, time, *, reason):
        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")

        if converted_time == -2:
            return await ctx.send("Time must be an integer")
        current_time = datetime.datetime.now()
        final_time = current_time + datetime.timedelta(seconds=converted_time)
        await self.bot.mongo["timer"]['remind'].insert_one(
            {"id": ctx.message.id, "user": ctx.author.id, "time": final_time, "reason": reason})
        await ctx.send(f"⏰ Reminder set! Reminder id: `{ctx.message.id}`")

    @remindme.command(name="delete", help="Delete an unwanted reminder")
    async def remindme_delete(self, ctx, remind_id: int):
        if await self.bot.mongo["timer"]['remind'].find_one({"id": remind_id}) is None:
            return await ctx.send("You don't have that reminder")
        await self.bot.mongo["timer"]['remind'].delete_one({"id": remind_id})
        await ctx.send("Reminder deleted!")

    @remindme.command(name="list", help="See your remind list")
    async def remindme_list(self, ctx):
        all_timer = self.bot.mongo["timer"]['remind'].find({'user': ctx.author.id})
        if all_timer is None:
            return await ctx.send("You don't have any reminders")
        data = []
        async for x in all_timer:
            data.append((f"ID - {x['id']}",
                         f"**End at:** <t:{int(datetime.datetime.timestamp(x['time']))}:R> **Reason:** {x['reason']}"))
        page = MenuPages(DefaultPageSource(f"Your reminder list", data), ctx)
        await page.start()

    @commands.group(help="List all the stuff you need to do", invoke_without_command=True, case_insensitive=True)
    async def todo(self, ctx):
        await ctx.send_help(ctx.command)

    @todo.command(help="Add a task to your todo list", aliases=['create'], name="add")
    async def todo_add(self, ctx, *, task):
        await self.bot.mongo["bot"]['todo'].insert_one(
            {"id": ctx.message.id, "user": ctx.author.id, "task": task})
        await ctx.send(f"TODO added! TODO id: `{ctx.message.id}`")

    @todo.command(name="delete", help="Delete a todo you complete")
    async def todo_delete(self, ctx, todo_id: int):
        if await self.bot.mongo["bot"]['todo'].find_one({"id": todo_id}) is None:
            return await ctx.send("You don't have that TODO")
        await self.bot.mongo["bot"]['todo'].delete_one({"id": todo_id})
        await ctx.send("Todo deleted!")

    @todo.command(name="edit", help="Edit a todo")
    async def todo_edit(self, ctx, todo_id: int, *, task):
        if await self.bot.mongo["bot"]['todo'].find_one({"id": todo_id}) is None:
            return await ctx.send("You don't have that TODO")
        await self.bot.mongo["bot"]['todo'].update_one({"id": todo_id}, {"$set": {"task": task}})
        await ctx.send("TODO edited!")

    @todo.command(name="list", help="See your todo list")
    async def todo_list(self, ctx):
        all_timer = self.bot.mongo["bot"]['todo'].find({'user': ctx.author.id})
        if all_timer is None:
            return await ctx.send("You don't have any TODO")
        data = []
        async for x in all_timer:
            data.append((f"ID - {x['id']}",
                         f"**Task:** {x['task']}"))
        page = MenuPages(DefaultPageSource(f"Your TODO list", data), ctx)
        await page.start()

    @commands.command(help="Suggest something to this bot")
    async def suggest(self, ctx, *, text):
        channel = self.bot.get_channel(887949939676684338)
        embed = discord.Embed(title="Incoming Suggestion", description=f"We got a suggestion from {ctx.author.mention}",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Text", value=f"```{text}```")
        embed.set_footer(text="To suggest something, do d!suggest <suggestion>")
        msg = await channel.send(embed=embed)
        await msg.add_reaction('🔼')
        await msg.add_reaction('🔽')
        await ctx.send("Message sent to the suggestion channel in our support server")

    @commands.command(help="Report a bug of the bot")
    async def bug(self, ctx, *, text):
        channel = self.bot.get_channel(921375785112195102)
        embed = discord.Embed(title="Incoming Bug Report", description=f"We got a bug reported by {ctx.author.mention}",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Text", value=f"```{text}```")
        embed.set_footer(text="To report a bug, do d!bug <bug>")
        await channel.send(embed=embed)
        await ctx.send("Message sent to the bug channel in our support server")
