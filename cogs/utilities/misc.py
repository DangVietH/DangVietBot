import discord
from discord.ext import commands, tasks
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import datetime
import aiohttp

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
timerdb = cluster["timer"]
timer = timerdb['remind']

snipe_message_content = None
snipe_message_author = None


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
        self.session = aiohttp.ClientSession(loop=bot.loop)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        global snipe_message_content
        global snipe_message_author

        snipe_message_content = message.content
        snipe_message_author = message.author
        await asyncio.sleep(60)
        snipe_message_author = None
        snipe_message_content = None

    @commands.command(help='See the last deleted message')
    async def snipe(self, ctx):
        if snipe_message_content is None:
            await ctx.send("Nothing to snipe for now")
        else:
            embed = discord.Embed(description=f"{snipe_message_content}", color=discord.Color.random())
            embed.set_author(name=f"{snipe_message_author}", icon_url=f"{snipe_message_author.avatar.url}")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

    @commands.command(help="Remind your task", aliases=["reminder"])
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

    @commands.command(help='See updated covid cases')
    async def covid(self, ctx, *, country="vietnam"):
        # some of this code base on https://github.com/Dhravya/Spacebot/blob/main/src/cogs/utility.py
        country = country.lower()
        url = await self.session.get(f"https://disease.sh/v3/covid-19/countries/{country}")
        stats = url.json()
        embed = discord.Embed(title=f"Covid Information in {stats['country']}",
                              description=f"Last updated: <t:{int(stats['updated'] / 1000)}:R>")
        embed.set_thumbnail(url=stats['flag'])
        embed.add_field(name="Total case", value=stats['cases'])
        embed.add_field(name="Today Cases", value=stats['todayCases'])
        embed.add_field(name="Total Deaths", value=stats['deaths'])
        embed.add_field(name="Today Death", value=stats['todayDeaths'])
        embed.add_field(name="Recovered", value=stats['todayCases'])
        embed.add_field(name="Today recovery", value=stats['todayRecovered'])
        embed.add_field(name="Total test", value=stats['tests'])
        embed.add_field(name="Active", value=stats['active'])
        embed.add_field(name="Critical", value=stats['critical'])
        embed.add_field(name="Cases Per One Million", value=stats['casesPerOneMillion'])
        embed.add_field(name="Deaths Per One Million", value=stats['activePerOneMillion'])
        embed.add_field(name="Recovered Per One Million", value=stats['recoveredPerOneMillion'])
        embed.add_field(name="Test Per One Million", value=stats['testsPerOneMillion'])
        await ctx.send(embed=embed)