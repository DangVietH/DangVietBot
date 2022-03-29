import discord
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
import datetime

cluster = AsyncIOMotorClient(config_var["mango_link"])
timer = cluster["timer"]['remind']


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


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time_checker.start()

    async def setup_hook(self) -> None:
        self.time_checker.start()

    @commands.group(help="Remind your task", aliases=["reminder"], invoke_without_command=True, case_insensitive=True)
    async def remind(self, ctx, time, *, reason):
        converted_time = convert(time)
        if converted_time == -1:
            await ctx.send("You didn't answer the time correctly")

        if converted_time == -2:
            await ctx.send("Time must be an integer")
        else:
            current_time = datetime.datetime.now()
            final_time = current_time + datetime.timedelta(seconds=converted_time)
            await timer.insert_one({"user": ctx.author.id, "time": final_time, "reason": reason})
            await ctx.send("⏰ Reminder set")

    @remind.command(help="See your remind list")
    async def list(self, ctx):
        all_timer = timer.find({'user': ctx.author.id})
        if all_timer is None:
            return await ctx.send("You don't have any reminders")
        embed = discord.Embed(title="Your remind list", color=self.bot.embed_color)
        async for x in all_timer:
            embed.add_field(name=f"End at: {x['time']}", value=f"**Reason:** {x['reason']}")
        await ctx.send(embed=embed)

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

    @commands.command(help="Poll")
    async def poll(self, ctx, question, *options: str):
        await ctx.channel.purge(limit=1)
        if len(options) <= 1:
            await ctx.send('Not enough options')
        if len(options) > 10:
            await ctx.send('This bot does not support polls with more than 10 options')
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description += '\n {} {} \n'.format(reactions[x], option)
        embed = discord.Embed(title=question, description=''.join(description), timestamp=ctx.message.created_at)
        embed.set_footer(text=f'Poll by {ctx.author}')
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)

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
