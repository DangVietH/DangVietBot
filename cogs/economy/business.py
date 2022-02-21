import nextcord as discord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
import asyncio

# load this file later


cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["economy"]
cursor = db["users"]
company = db["company"]


class Business(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Company commands")
    @commands.guild_only()
    async def company(self, ctx):
        embed = discord.Embed(title="Company commands", color=discord.Color.random())
        command = self.bot.get_command("company")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"company {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @company.command(help="Create a company")
    async def create(self, ctx):
        questions = ["What is the company name:",
                     "What is the company description:",
                     "What is the company logo (image link only):"]

        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)

            try:
                msg = await self.bot.wait_for('message', timeout=600.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Type Faster Next Time!")
                return
            else:
                answers.append(msg.content)

        check = await company.find_one({"name": str(answers[0])})
        if check:
            await ctx.send("Company name already exists")
            return

        await company.insert_one({
            "name": str(answers[0]),
            "description": str(answers[1]),
            "logo": str(answers[2]),
            "owner": ctx.author.id,
            "revenue": 1000
        })
        await ctx.send(f"Your new company has been created. Time for some shady business!")