import nextcord as discord
from nextcord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
import asyncio
from cogs.economy.economy import Economy

# load this file later


cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["economy"]
cursor = db["users"]
company = db["company"]

industries = [
    "Agriculture",
    "Automotive",
    "Banking",
    "Chemicals",
    "Computers",
    "Construction",
    "Education",
    "Electronics",
    "Energy",
    "Entertainment",
    "Finance",
    "Food",
    "Healthcare",
    "Insurance",
    "Manufacturing",
    "Media",
    "Retail",
    "Technology",
    "Telecommunications",
    "Transportation",
    "Utilities"
]


class Business(commands.Cog):
    @commands.command(help="List all industries")
    async def industryList(self, ctx):
        embed = discord.Embed(title="Industries", color=discord.Color.random(), description="\n".join([f"{i}" for i in industries]))
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Company commands")
    @commands.guild_only()
    async def company(self, ctx):
        embed = discord.Embed(title="Company commands", color=discord.Color.random())
        command = self.bot.get_command("company")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"company {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @company.command(help="Create a company", aliases=["create"])
    async def register(self, ctx):
        questions = ["What is the company name:",
                     "What is the company description:",
                     "What is the company logo (image link only):",
                     "What type of industries does the company belong to (to find you industry, do industryList):"]

        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)

            try:
                msg = await self.bot.wait_for('message', timeout=600.0, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("Type Faster Next Time!")
            else:
                answers.append(msg.content)

        if await company.find_one({"name": str(answers[0])}):
            return await ctx.send("Company name already exists")

        if str(answers[0]).lower() not in industries:
            return await ctx.send("Invalid industry. Please use the industryList command to find your industry")

        await company.insert_one({
            "name": str(answers[0]).lower(),
            "description": str(answers[1]),
            "logo": str(answers[2]),
            "industry": str(answers[3]),
            "ceo": ctx.author.id,
            "revenue": 1000,
            "stock amount": 100,
            "stock value": 0
        })
        await ctx.send(f"Your new company has been created. Time for some shady business!")

    @company.command(help="View a company", aliases=["view"])
    async def info(self, ctx, *, name):
        name = name.lower()
        check = await company.find_one({"name": name})
        if check is None:
            return await ctx.send("Company not found")
        embed = discord.Embed(title=f"{check['name']}", color=discord.Color.random(), description=f"{check['description']}")
        embed.set_thumbnail(url=check['logo'])
        embed.add_field(name="CEO", value=f"{self.bot.get_user(check['ceo'])}")
        embed.add_field(name="Revenue", value=f"{check['revenue']}")
        embed.add_field(name="Industry", value=f"{check['industry']}")
        await ctx.send(embed=embed)