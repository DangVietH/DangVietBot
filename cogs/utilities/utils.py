import discord
from discord.ext import commands, tasks
from motor.motor_asyncio import AsyncIOMotorClient
from utils import config_var
import datetime

cluster = AsyncIOMotorClient(config_var["mango_link"])
timer = cluster["timer"]['remind']
afk = cluster["timer"]['afk']


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
    def __init__(self, bot):
        self.bot = bot
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

    @commands.Cog.listener()
    async def on_message(self, message):
        if await afk.find_one({"guild": message.guild.id, "member": message.author.id}):
            await afk.delete_one({"guild": message.guild.id, "member": message.author.id})
            await message.channel.send(f"{message.author.mention}, I have remove your afk")
        if message.mentions:
            for mention in message.mentions:
                is_afk = await afk.find_one({"guild": message.guild.id, "member": mention.id})
                if is_afk:
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
