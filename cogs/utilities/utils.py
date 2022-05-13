import discord
from discord.ext import commands, tasks, menus
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


class GuildCasePageSource(menus.ListPageSource):
    def __init__(self, casenum, data):
        self.casenum = casenum
        super().__init__(data, per_page=4)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.red(), title=f"List of cases in {menu.ctx.author.guild.name}", description=f"**Total case:** {self.casenum}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class UserCasePageSource(menus.ListPageSource):
    def __init__(self, member, casenum, data):
        self.member = member
        self.casenum = casenum
        super().__init__(data, per_page=4)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.red(), title=f"List of {self.member} cases", description=f"**Total case:** {self.casenum}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Utils(commands.Cog):
    emoji = "📝"

    def __init__(self, bot):
        self.bot = bot
        self.time_checker.start()

    async def cog_unload(self):
        self.time_checker.cancel()

    @commands.command(help="Look at server moderation cases", aliases=["case"])
    async def caselist(self, ctx):
        results = await self.bot.mongo["moderation"]['cases'].find_one({"guild": ctx.guild.id})
        gdata = []
        if len(results['cases']) < 1:
            return await ctx.send("Looks like all your server members are good people! Good job!")
        for case in results['cases']:
            gdata.append((f"Case {case['Number']}",
                          f"**Type:** {case['type']}\n **User:** {self.bot.get_user(int(case['user']))}\n**Mod:** {self.bot.get_user(int(case['Mod']))}\n**Reason:** {case['reason']}"))
        page = MenuPages(GuildCasePageSource(results['num'], gdata), ctx)
        await page.start()

    @commands.command(help="Look at user moderation cases")
    async def casesfor(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        udata = []
        user_check = await self.bot.mongo["moderation"]['user'].find_one({"guild": ctx.guild.id, "user": member.id})
        results = await self.bot.mongo["moderation"]['cases'].find_one({"guild": ctx.guild.id})
        if user_check is None:
            return await ctx.send("Looks like a good person 🥰")
        for case in results['cases']:
            if member.id == int(case['user']):
                udata.append((f"Case {case['Number']}",
                              f"**Type:** {case['type']}\n**Mod:** {self.bot.get_user(int(case['Mod']))}\n**Reason:** {case['reason']}"))

        page = MenuPages(UserCasePageSource(member, user_check['total_cases'], udata), ctx)
        await page.start()

    @commands.group(help="Remind a task you want to complete", invoke_without_command=True, case_insensitive=True, aliases=['reminder', 'remind', 'notify'])
    async def remindme(self, ctx, time, *, reason):
        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")

        if converted_time == -2:
            return await ctx.send("Time must be an integer")
        current_time = datetime.datetime.now()
        final_time = current_time + datetime.timedelta(seconds=converted_time)
        await self.bot.mongo["timer"]['remind'].insert_one({"id": ctx.message.id, "user": ctx.author.id, "time": final_time, "reason": reason})
        await ctx.send("⏰ Reminder set")

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
            data.append((f"ID - {x['id']}", f"**End at:** <t:{int(datetime.datetime.timestamp(x['time']))}:R> **Reason:** {x['reason']}"))
        page = MenuPages(DefaultPageSource(f"Your reminder list", data), ctx)
        await page.start()

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
                if is_afk is not None:
                    await message.channel.send(f"`{mention}` is currently afk! Reason: **{is_afk['reason']}**")

    @commands.command(help="Tell people that ur gone")
    async def afk(self, ctx, *, reason="Poop"):
        if await self.bot.mongo["timer"]['afk'].find_one({"guild": ctx.guild.id, "member": ctx.author.id}) is not None:
            return await ctx.send("You're already afk")
        await self.bot.mongo["timer"]['afk'].insert_one({"guild": ctx.guild.id, "member": ctx.author.id, "reason": reason})
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
        embed = discord.Embed(title="Incoming Bug Report", description=f"We got a bug reported by {ctx.author.mention}",
                              color=discord.Color.from_rgb(225, 0, 92))
        embed.add_field(name="Text", value=f"```{text}```")
        embed.set_footer(text="To report a bug, do d!bug <bug>")
        await channel.send(embed=embed)
        await ctx.send("Message sent to the bug channel in our support server")
