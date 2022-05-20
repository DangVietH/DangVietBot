import discord
from discord.ext import commands
from utils import DefaultPageSource, MenuPages
import datetime


class Tags(commands.Cog):
    emoji = "🏷"

    def __init__(self, bot):
        self.bot = bot
        self.cursor = self.bot.mongo["bot"]["tag"]

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Tag setup")
    async def tag(self, ctx, *, name=None):
        if name is None:
            return await ctx.send_help(ctx.command)
        check = await self.cursor.find_one({"guild": ctx.guild.id})
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
        msg = await ctx.send("Please answer the following questions:")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await msg.edit(content=question)
            user_msg = await self.bot.wait_for('message', check=check)
            answers.append(user_msg.content)
            await ctx.channel.purge(limit=1)
        check = await self.cursor.find_one({"guild": ctx.guild.id})
        if check is None:
            await self.cursor.insert_one({"guild": ctx.guild.id, "tag": [
                {"name": answers[0], "value": answers[1], "owner": ctx.author.id}
            ]})
            await msg.edit(content=f"Tag {answers[0]} successfully created")
        else:
            is_exist = await self.cursor.find_one({"guild": ctx.guild.id, "tag.name": answers[0]})
            if is_exist is not None:
                await msg.edit(content="Tag already exist. Remember that tag name are case SENSITIVE")
            else:
                await self.cursor.update_one({"guild": ctx.guild.id}, {
                    "$addToSet": {"tag": {"name": answers[0], "value": answers[1], "owner": ctx.author.id, "created": datetime.datetime.utcnow()}}})
                await msg.edit(content=f"Tag {answers[0]} successfully created")

    @tag.command(help="Remove a tag", aliases=['remove'])
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx, *, name):
        if await self.cursor.find_one({"guild": ctx.guild.id, "tag.name": name}) is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        await self.cursor.update_one({"guild": ctx.guild.id}, {"$pull": {"tag": {"name": name}}})
        await ctx.send("Tag deleted successfully")

    @tag.command(help="Edit a tag")
    async def edit(self, ctx, *, name):
        gcheck = await self.cursor.find_one({"guild": ctx.guild.id})
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
        await self.cursor.update_one({"guild": ctx.guild.id, "tag.name": name}, {"$set": {"tag.$.value": user_choice}})
        await ctx.send("Tag edited successfully")

    @tag.command(help="See a list of tags")
    async def list(self, ctx):
        check = await self.cursor.find_one({"guild": ctx.guild.id})
        if check is None:
            await ctx.send("No tags in here")
        else:
            data = []
            ta = check['tag']
            for thing in ta:
                to_append = (thing['name'], f"**Owner:** {self.bot.get_user(thing['owner'])}")
                data.append(to_append)
            page = MenuPages(DefaultPageSource(f"Tags of {ctx.guild.name}", data), ctx)
            await page.start()

    @tag.command(help="Claim a tag", name="claim")
    async def tagclaim(self, ctx, *, name):
        check = await self.cursor.find_one({"guild": ctx.guild.id})
        if check is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        tnname = None
        owner = None
        for thing in check['tag']:
            if thing['name'] == name:
                tnname = thing['name']
                owner = thing['owner']
                break
        if tnname is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")

        is_owner_in_server = ctx.guild.get_member(owner)
        if is_owner_in_server is not None:
            return await ctx.send("Tag owner is still in server")
        await self.cursor.update_one({"guild": ctx.guild.id, "tag.name": name}, {"$set": {"tag.$.owner": ctx.author.id}})
        await ctx.send("Tag claimed successfully")

    @tag.command(help="Give a tag to someone", name="trade", aliases=["transfer", "give"])
    async def tagtrade(self, ctx, member: discord.Member, *, name):
        check = await self.cursor.find_one({"guild": ctx.guild.id})
        if check is None:
            return await ctx.send("No tags to claim")
        tnname = None
        owner = None
        for thing in check['tag']:
            if thing['name'] == name:
                tnname = thing['name']
                owner = thing['owner']
                break
        if tnname is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        if ctx.author.id != owner:
            return await ctx.send("That tag needs to be owned by you.")
        await self.cursor.update_one({"guild": ctx.guild.id, "tag.name": name}, {"$set": {"tag.$.owner": member.id}})
        await ctx.send("Tag traded successfully")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        check = await self.cursor.find_one({"guild": guild.id})
        if check is not None:
            await self.cursor.delete_one({"guild": guild.id})