import discord
from discord.ext import commands
import aiohttp
import random
import asyncio


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Play some quizs", aliases=["quiz"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trivia(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://opentdb.com/api.php?amount=1") as resp:
                data = await resp.json()

        embed = discord.Embed(color=self.bot.embed_color)
        ldt = data['results'][0]
        ques = ldt["incorrect_answers"]
        corret_ans = ldt["correct_answer"]
        ques.append(corret_ans)
        random.shuffle(ques)
        embed.title = ldt["question"].replace("&quot;", "'").replace("&#039;", "'")
        embed.description = f"Answer this in 30 seconds:\n**1.** {ques[0]}\n**2.** {ques[1]}\n**3.** {ques[2]}\n**4.** {ques[3]}"
        await ctx.send(embed=embed)

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"Time's out! The correct answer was {corret_ans}")
        else:
            emb2 = discord.Embed()
            if msg.content != corret_ans:
                emb2.title = "Incorrect"
                emb2.description = f"The correct answer was {corret_ans}"
                emb2.color = discord.Color.red()
                await ctx.send(embed=emb2)
                return
            embed.title = "Correct"
            embed.color = discord.Color.green()
            await ctx.send(embed=embed)

    @commands.command()
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
