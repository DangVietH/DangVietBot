import discord
from discord.ext import commands, menus
from utils import config_var, MenuPages
import datetime


class LyricPageSource(menus.ListPageSource):
    def __init__(self, title, url, thumbnail, data):
        self.title = title
        self.url = url
        self.thumbnail = thumbnail
        super().__init__(data, per_page=20)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=menu.ctx.bot.embed_color, url=self.url)
        embed.description = "\n".join([part for part in entries])
        embed.set_thumbnail(url=self.thumbnail)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class GuildCasePageSource(menus.ListPageSource):
    def __init__(self, casenum, data):
        self.casenum = casenum
        super().__init__(data, per_page=2)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.red(), title=f"List of cases in {menu.ctx.author.guild.name}",
                              description=f"**Total case:** {self.casenum}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class UserCasePageSource(menus.ListPageSource):
    def __init__(self, member, casenum, data):
        self.member = member
        self.casenum = casenum
        super().__init__(data, per_page=2)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.red(), title=f"List of {self.member} cases",
                              description=f"**Total case:** {self.casenum}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Misc(commands.Cog):
    emoji = "🛠"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Look at server moderation cases", aliases=["case"])
    async def caselist(self, ctx):
        results = await self.bot.mongo["moderation"]['cases'].find_one({"guild": ctx.guild.id})
        gdata = []
        if len(results['cases']) < 1:
            return await ctx.send("Looks like all your server members are good people! Good job!")
        for case in results['cases']:
            gdata.append(
                (
                    f"Case {case['Number']}",
                    f"**Type:** {case['type']}\n **User:** {case['user']} ({case['user_id']})\n**Mod:** {case['Mod']}\n**Reason:** {case['reason']}\n**Date:** <t:{int(datetime.datetime.timestamp(case['time']))}>"
                )
            )
        page = MenuPages(GuildCasePageSource(results['num'], gdata), ctx)
        await page.start()

    @commands.command(help="Look at user moderation cases")
    async def casesfor(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        udata = []
        user_check = await self.bot.mongo["moderation"]['user'].find_one({"guild": ctx.guild.id, "user_id": member.id})
        results = await self.bot.mongo["moderation"]['cases'].find_one({"guild": ctx.guild.id})
        if user_check is None:
            return await ctx.send("Looks like a good person 🥰")
        for case in results['cases']:
            if member.id == int(case['user_id']):
                udata.append(
                    (f"Case {case['Number']}",
                     f"**Type:** {case['type']}\n**Mod:** {case['Mod']}\n**Reason:** {case['reason']}\n**Date:** <t:{int(datetime.datetime.timestamp(case['time']))}"
                     ))

        page = MenuPages(UserCasePageSource(member, user_check['total_cases'], udata), ctx)
        await page.start()

    @commands.command(aliases=['lyrc', 'lyric'], help="Shows the lyrics of a song")
    async def lyrics(self, ctx, *, song):
        await ctx.channel.typing()
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/lyrics", params={"title": song}
        )
        data = await resp.json()

        if data.get('error'):
            return await ctx.send(f"Error: {data['error']}")
        pagData = []
        for chunk in data['lyrics'].split('\n'):
            pagData.append(chunk)
        page = MenuPages(
            LyricPageSource(data['title'], data['links']['genius'], data['thumbnail']['genius'], pagData),
            ctx)
        await page.start()

    @commands.command(help="Show weather info for a city")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def weather(self, ctx, *, city):
        resp = await self.bot.session.get(
            "http://api.weatherapi.com/v1/current.json", params={"key": config_var['weather'], "q": city}
        )
        data = await resp.json()
        if data.get('error'):
            return await ctx.send(f"Sorry, that city doesn't exist")
        embed = discord.Embed(
            title=f"Weather for {data['location']['name']} - {data['current']['condition']['text']}",
            description=f"{data['location']['name']}, {data['location']['country']} <t:{data['location']['localtime_epoch']}>\n {data['current']['condition']['text']}",
            color=self.bot.embed_color
        ).add_field(
            name="Current Conditions",
            value=(
                f"**Temperature**: {data['current']['temp_c']}°C\n"
                f"**Humidity**: {data['current']['humidity']}%\n"
                f"**Wind speed**: {data['current']['wind_kph']}kph\n"
                f"**Cloud**: {data['current']['cloud']}%\n"
            )
        )
        embed.set_thumbnail(url=f"https:{data['current']['condition']['icon']}")
        await ctx.send(embed=embed)