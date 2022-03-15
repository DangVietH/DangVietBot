import nextcord as discord
from nextcord.ext import commands, menus
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from utils.menuUtils import ViewMenuPages
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["bot"]["tag"]


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
        questions = ["What is the tag name: ",
                     "What is the tag value: "]
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
        is_exist = await cursor.find_one({"guild": ctx.guild.id, "tag.name": name})
        if is_exist is None:
            await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        else:
            await cursor.update_one({"guild": ctx.guild.id}, {"$pull": {"tag": {"name": name}}})
            await ctx.send("Tag deleted successfully")

    @tag.command(help="Edit a tag")
    async def edit(self, ctx, *, name):
        is_exist = await cursor.find_one({"guild": ctx.guild.id, "tag.name": name})
        if is_exist is None:
            return await ctx.send("Tag not found. Remember that tag name are case SENSITIVE")
        if ctx.author is not self.bot.get_user(is_exist['owner']):
            return await ctx.send("You are not the owner of this tag")
        await ctx.send("What is the new tag value: `Type end to abort the process`")

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        user_choice = (await self.bot.wait_for('message', check=check)).content
        if user_choice == "end":
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
            page = ViewMenuPages(source=TagPageSource(data), disable_buttons_after=True, ctx=ctx)
            await page.start(ctx)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        check = await cursor.find_one({"guild": guild.id})
        if check is not None:
            await cursor.delete_one({"guild": guild.id})