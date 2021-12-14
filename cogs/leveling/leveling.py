import discord
from discord.ext import commands, menus
import os
from motor.motor_asyncio import AsyncIOMotorClient

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]
levelling = db['member']
disable = db['disable']
role = db['roles']
upchannel = db['channel']


class MenuButtons(discord.ui.View, menus.MenuPages):
    def __init__(self, source):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None

    async def start(self, ctx, *, channel=None, wait=False):
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        value = await super()._get_kwargs_from_page(page)
        if 'view' not in value:
            value.update({'view': self})
        return value

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.green)
    async def first_page(self, payload):
        await self.show_page(0)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.green)
    async def previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(emoji='⏹', style=discord.ButtonStyle.green)
    async def on_stop(self, payload):
        self.stop()

    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.green)
    async def next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.green)
    async def last_page(self, payload):
        max_pages = self._source.get_max_pages()
        last_page = max(max_pages - 1, 0)
        await self.show_page(last_page)


class GuildLeaderboardPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=12)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=f"🏆 Leaderboard of {menu.ctx.author.guild.name}", color=discord.Color.green())
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class GlobalLeaderboardPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=12)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url="https://cdn.discordapp.com/attachments/900197917170737152/916598584005238794/world.png",
            name="Global Leaderboard")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            if not message.author.bot:
                is_disabled = await disable.find_one({"guild": message.guild.id})
                if is_disabled is None:
                    stats = await levelling.find_one({'guild': message.guild.id, "user": message.author.id})
                    if stats is None:
                        insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 5}
                        await levelling.insert_one(insert)
                    else:
                        add_exp = stats['xp'] + 5
                        await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                                   {"$set": {"xp": add_exp}})
                        lvl_end = int(stats['xp'] ** (1 / 4))
                        if stats['level'] < lvl_end:
                            new_lvl = stats['level'] + 1
                            await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                                       {"$set": {"level": new_lvl}})
                            lvl_channel = await upchannel.find_one({"guild": message.guild.id})
                            if lvl_channel is None:
                                await message.channel.send(f"🎉 {message.author.mention} has reached level **{new_lvl}**!!🎉")
                            else:
                                channel = self.bot.get_channel(lvl_channel["channel"])
                                await channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")
                else:
                    return None

    @commands.command(help="Disable levelling")
    @commands.has_permissions(administrator=True)
    async def disable_level(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await ctx.send("Bruh")
        else:
            insert = {"guild": ctx.guild.id}
            await disable.insert_one(insert)
            for member in ctx.guild.members:
                if not member.bot:
                    result = await levelling.find_one({"guild": ctx.guild.id, "user": member.id})
                    if result is not None:
                        await levelling.delete_one({"guild": ctx.guild.id, "user": member.id})
            await ctx.send('Levelling disabled')

    @commands.command(help="Re-enable levelling")
    @commands.has_permissions(administrator=True)
    async def renable_level(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await disable.delete_one(check)
            await ctx.send('Levelling re-enable')
        else:
            await ctx.send('Leveling already enabled')

    @commands.command(help="See your rank")
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        stats = await levelling.find_one({'guild': ctx.guild.id, "user": user.id})
        if stats is not None:
            ranking = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
            rank = 0
            async for x in ranking:
                rank += 1
                if stats['user'] == x['user']:
                    break

            embed = discord.Embed(title=user, color=user.color)
            embed.add_field(name="Level", value=f"#{stats['level']}")
            embed.add_field(name="XP", value=f"#{stats['xp']}")
            embed.add_field(name="Rank", value=f"#{rank}")
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")

    @commands.command(help="See server ranks")
    async def top(self, ctx):
        stats = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {ctx.guild.get_member(x['user'])}", f"**Level:** {x['level']} \n**XP:** {x['xp']}")
            data.append(to_append)

        pages = MenuButtons(GuildLeaderboardPageSource(data))
        await pages.start(ctx)

    @commands.command(help="See global rank")
    async def gtop(self, ctx):
        stats = levelling.find().sort("xp", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {self.bot.get_user(x['user'])}", f"**Server:** {self.bot.get_guild(x['guild'])} \n**Level:** {x['level']} \n**XP:** {x['xp']}")
            data.append(to_append)

        pages = MenuButtons(GlobalLeaderboardPageSource(data))
        await pages.start(ctx)

    @commands.command(help="Setup level up channel if you like to")
    @commands.has_permissions(administrator=True)
    async def lvl_channel(self, ctx, channel: discord.TextChannel):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await upchannel.insert_one(insert)
            await ctx.send(f"Level up channel set to {channel.mention}")
        elif result is not None:
            await upchannel.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Level up channel updated to {channel.mention}")

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                result = await levelling.find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await levelling.delete_one({"guild": guild.id, "user": member.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await levelling.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await levelling.delete_one({"guild": member.guild.id, "user": member.id})