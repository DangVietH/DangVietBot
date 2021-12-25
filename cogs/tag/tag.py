from discord.ext import commands, menus
import discord
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from utils.menustuff import MenuButtons

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["bot"]
cursor = db["tag"]


class TagPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green(), title=f"{menu.ctx.author.guild.name} Tags")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Tag setup")
    async def tag(self, ctx, *, name=None):
        if name is None:
            embed = discord.Embed(title="Tag command", color=discord.Color.random(), description="Set up custom prefix")
            command = self.bot.get_command("tag")
            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    embed.add_field(name=f"tag {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
            await ctx.send(embed=embed)
        else:
            check = await cursor.find_one({"guild": ctx.guild.id})
            if check is None:
                return None
            else:
                all_tag = check['tag']
                for thing in all_tag:
                    if thing['name'] == name:
                        await ctx.send(thing['value'])
                        break

    @tag.command(help="Create a tag")
    async def create(self, ctx):
        await ctx.send("Answer These Question In 10 minute!")
        questions = ["What is the tag name \n`Type end to abort the process`: ", "What is the tag value \n`Type end to abort the process`: "]
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

        end = "end"
        if answers[0] == end.lower() or answers[1] == end.lower():
            await ctx.send()
        check = await cursor.find_one({"guild": ctx.guild.id})
        if check is None:
            await cursor.insert_one({"guild": ctx.guild.id, "tag": [
                {"name": answers[0], "value": answers[1], "owner": ctx.author.id}
            ]})
            await ctx.send(f"Tag {answers[0]} successfully created")
        else:
            is_exist = await cursor.find_one({"guild": ctx.guild.id, "tag.name": answers[0]})
            if is_exist is not None:
                await ctx.send("Tag already exist. Remember that tag name are case SENSITIVE")
            else:
                await cursor.update_one({"guild": ctx.guild.id}, {
                    "$push": {"tag": {"name": answers[0], "value": answers[1], "owner": ctx.author.id}}})
                await ctx.send(f"Tag {answers[0]} successfully created")

    @tag.command(help="Remove a tag", aliases=['remove'])
    async def delete(self, ctx, *, name):
        is_exist = await cursor.find_one({"guild": ctx.guild.id, "tag.name": name})
        if is_exist is None:
            await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        else:
            await cursor.update_one({"guild": ctx.guild.id}, {"$pull": {"tag": {"name": name}}})
            await ctx.send("Tag deleted successfully")

    @tag.command(help="Edit a tag")
    async def edit(self, ctx, *, name):
        await ctx.send("Complete this in 10 minute!")
        questions = ["What is the new value: "]
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
        is_exist = await cursor.find_one({"guild": ctx.guild.id, "tag.name": name})
        if is_exist is None:
            await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        else:
            await cursor.update_one({"guild": ctx.guild.id, "tag.name": name},
                                    {"$set": {"tag.$.value": answers[0]}})
            await ctx.send("Tag edit successfully")

    @tag.command(help="See a list of tags")
    async def list(self, ctx):
        check = await cursor.find_one({"guild": ctx.guild.id})
        if check is None:
            await ctx.send("No tags in here")
        else:
            data = []
            ta = check['tag']
            for thing in ta:
                to_append = (thing['name'], f"**Owner:** {self.bot.get_user(thing['owner'])}")
                data.append(to_append)
            page = MenuButtons(TagPageSource(data))
            await page.start(ctx)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        check = await cursor.find_one({"guild": guild.id})
        if check is not None:
            await cursor.delete_one({"guild": guild.id})