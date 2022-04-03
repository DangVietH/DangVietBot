import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.menuUtils import MenuPages
from utils.menuUtils import DefaultPageSource
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["bot"]["tag"]

# beware! terrible code ahead


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Tag setup")
    async def tag(self, ctx, *, name=None):
        if name is None:
            _cmd = self.bot.get_command("help")
            await _cmd(ctx, command='tag')
        else:
            check = await cursor.find_one({"guild": ctx.guild.id})
            if check is None:
                return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

            all_tag = check['tag']
            value = None
            for thing in all_tag:
                if thing['name'] == name:
                    value = thing['value']
                    break
            if value is None:
                return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

            await ctx.send(value)

    @tag.command(help="Create a tag")
    async def create(self, ctx):
        questions = ["What is the tag name: ",
                     "What is the tag value: "]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)
            msg = await self.bot.wait_for('message', timeout=600.0, check=check)
            answers.append(msg.content)
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
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx, *, name):
        if await cursor.find_one({"guild": ctx.guild.id, "tag.name": name}) is None:
            await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        else:
            await cursor.update_one({"guild": ctx.guild.id}, {"$pull": {"tag": {"name": name}}})
            await ctx.send("Tag deleted successfully")

    @tag.command(help="Edit a tag")
    async def edit(self, ctx, *, name):
        gcheck = await cursor.find_one({"guild": ctx.guild.id})
        if gcheck is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

        tnname = None
        owner = None
        for thing in gcheck['tag']:
            if thing['name'] == name:
                tnname = thing['name']
                owner = thing['owner']
                break

        if tnname is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

        if ctx.author.id != owner:
            return await ctx.send("You are not the owner of this tag")
        await ctx.send("What is the new tag value: `Type end to abort the process`")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        user_choice = (await self.bot.wait_for('message', check=check)).content
        if user_choice == "end".lower():
            return await ctx.send("Task abort successfully")
        await cursor.update_one({"guild": ctx.guild.id, "tag.name": name}, {"$set": {"tag.value": user_choice}})
        await ctx.send("Tag edited successfully")

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
            page = MenuPages(DefaultPageSource(f"Tags of {ctx.guild.name}", data))
            await page.start(ctx)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        check = await cursor.find_one({"guild": guild.id})
        if check is not None:
            await cursor.delete_one({"guild": guild.id})