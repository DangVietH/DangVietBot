from googletrans import Translator
from discord.ext import commands
import discord
import asyncio


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Translate a messages")
    async def translate(self, ctx, lang, *, args):
        t = Translator()
        a = t.translate(args, dest=lang)
        await ctx.send(a.text)

    @commands.command(help="Remind your task", aliases=["reminder"])
    async def remind(self, ctx, time, *, task):
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
        converted_time = convert(time)
        if converted_time == -1:
            await ctx.send("You didn't answer the time correctly")

        if converted_time == -2:
            await ctx.send("Time must be an integer")

        await ctx.send("⏰ Reminder set")
        await asyncio.sleep(converted_time)
        await ctx.author.send(f"Reminder: {task}")

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


def setup(bot):
    bot.add_cog(Misc(bot))
