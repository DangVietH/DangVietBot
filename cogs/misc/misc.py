import discord
from discord.ext import commands, menus
from utils import config_var, MenuPages


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


class Misc(commands.Cog):
    emoji = "🛠"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['lyrc', 'lyric'], help="Shows the lyrics of a song")
    async def lyrics(self, ctx, *, song):
        await ctx.channel.typing()
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/lyrics", params={"title": song}
        )
        data = await resp.json()

        if data.get('error'):
            return await ctx.send(f"Received unexpected error: {data['error']}")
        pagData = []
        for chunk in data['lyrics'].split('\n'):
            pagData.append(chunk)
        page = MenuPages(
            LyricPageSource(data['title'], data['links']['genius'], data['thumbnail']['genius'], pagData),
            ctx)
        await page.start()

    @commands.command(help="Show weather info for a city")
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
                f"**Wind speed**: {data['current']['wind_mph']}mph\n"
                f"**Cloud**: {data['current']['cloud']}%\n"
            )
        )
        embed.set_thumbnail(url=f"https:{data['current']['condition']['icon']}")
        await ctx.send(embed=embed)