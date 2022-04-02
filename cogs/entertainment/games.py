import discord
from discord.ext import commands
import aiohttp
import random
import asyncio


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Play some test quizs")
    @commands.is_owner()
    async def testtrivia(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://opentdb.com/api.php?amount=1") as resp:
                data = await resp.json()

    @commands.command(help="Play some quizs", aliases=["quiz"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trivia(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://opentdb.com/api.php?amount=1") as resp:
                data = await resp.json()

        if data['response_code'] != 0:
            return await ctx.send("There was an error fetching the question! Just rerun the command")

        embed = discord.Embed(color=self.bot.embed_color)
        ldt = data['results'][0]
        ques = ldt["incorrect_answers"]
        corret_ans = ldt["correct_answer"].replace("&quot;", "'").replace("&#039;", "'")
        ques.append(corret_ans)
        random.shuffle(ques)
        embed.title = ldt["question"].replace("&quot;", "'").replace("&#039;", "'")
        embed.description = f"Answer this in 30 seconds:\n**1:** {ques[0]}\n**2:** {ques[1]}\n**3:** {ques[2]}\n**4:** {ques[3]}\nType the correct options (example:`1`)"
        embed.set_footer(text=f"Category: {ldt['category']} | Difficulty: {ldt['difficulty']}")
        await ctx.send(embed=embed)
        opList = ['1', '2', '3', '4']

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"Time's out! The correct answer was {corret_ans}")
        else:
            if msg.content.lower() not in opList:
                return await ctx.send("Invalid option! It's needs to be like `1`, `2`, `3` or `4`")
            emb2 = discord.Embed(timestamp=ctx.message.created_at)
            for i in range(len(opList)):
                if msg.content.lower() == opList[i]:
                    choice = ques[i]
                    if choice != corret_ans:
                        emb2.title = "Incorrect"
                        emb2.description = f"The correct answer is **{corret_ans}**"
                        emb2.color = discord.Color.red()
                        await ctx.send(embed=emb2)
                        return
                    emb2.title = "Correct"
                    emb2.description = f"The correct answer indeed is **{corret_ans}**"
                    emb2.color = self.bot.embed_color
                    await ctx.send(embed=emb2)

    @commands.command(help="Play rock paper scissors with me")
    async def rps(self, ctx, choice):
        choice = choice.lower()
        choices = ["rock", "paper", "scissors"]
        if choice not in choices:
            return await ctx.send("Please only put rock, paper or scissors")
        rchoices = random.choice(choices)
        embed = discord.Embed(title="Rock Paper Scissors", color=self.bot.embed_color)
        if choice == 'rock':
            if rchoices == 'rock':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**It's a tie!**"
                await ctx.send(embed=embed)
            elif rchoices == 'paper':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**I won!**"
                await ctx.send(embed=embed)
            elif rchoices == 'scissors':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**You won!**"
                await ctx.send(embed=embed)

        elif choice == 'paper':
            if rchoices == 'rock':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**You won!**"
                await ctx.send(embed=embed)
            elif rchoices == 'paper':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**It's a tie!**"
                await ctx.send(embed=embed)
            elif rchoices == 'scissors':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**I won!**"
                await ctx.send(embed=embed)

        elif choice == 'scissors':
            if rchoices == 'rock':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**I won!**"
                await ctx.send(embed=embed)
            elif rchoices == 'paper':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**You won!**"
                await ctx.send(embed=embed)
            elif rchoices == 'scissors':
                embed.description = f"I choose **{rchoices}**\nYou choose **{choice}**\n**It's a tie!**"
                await ctx.send(embed=embed)