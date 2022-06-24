import discord
from discord.ext import commands
import io


class Image(commands.Cog):
    emoji = "🖼"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Show your gay pride")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/lgbt", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"gay.png"
        ))

    @commands.command(help="Get a horny permission's card")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def horny(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/horny", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"horny.png"
        ))

    @commands.command(help="U R arrested")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jail(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/jail", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"jail.png"
        ))

    @commands.command(help="GET TRIGGERED")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def triggered(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/triggered", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"triggered.gif"
        ))

    @commands.command(help="ur tracking me right")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ads(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/ads", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"ads.png"
        ))

    @commands.command(help="ur very cute", aliases=['patpat'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def petpet(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/patpat", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"petpet.gif"
        ))

    @commands.command(help="Steamy stuff")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def boil(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/boil", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"boil.gif"
        ))

    @commands.command(help="You just see the worst shit ever")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def canny(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/canny", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"canny.png"
        ))

    @commands.command(help="Waving in the wind")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cloth(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/cloth", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"cloth.gif"
        ))

    @commands.command(help="UR terrible")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def cartoon(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/cartoon", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"cartoon.png"
        ))

    @commands.command(help="The best album ever")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def explicit(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/explicit", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"explicit.png"
        ))

    @commands.command(help="Say sumthing")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def tv(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/tv", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"tv.gif"
        ))

    @commands.command(help="shoot em")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def shoot(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/shoot", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"shoot.gif"
        ))

    @commands.command(help="Depressing")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rain(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/rain", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"rain.gif"
        ))

    @commands.command(help="tic tic tic")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def clock(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/clock", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"clock.gif"
        ))

    @commands.command(help="Umm we have a tech problem")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def glitch(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/glitch", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"glitch.gif"
        ))

    @commands.command(help="You turn into tiny particles", aliases=["particles"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def balls(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/balls", params={"image_url": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"balls.gif"
        ))

    @commands.command(help="Yall be drippin")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def drip(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://api.popcat.xyz/drip", params={"image": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"drip.png"
        ))

    @commands.command(help="Make a fake youtube video", aliases=['ytvideo'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ytvid(self, ctx, member: discord.Member = None, *, title="Sus"):
        resp = await self.bot.session.get(
            f"https://api.jeyy.xyz/image/youtube", params={
                "avatar_url": member.display_avatar.url,
                "title": title,
                "author": member.display_name
            }
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"ytvid.gif"
        ))

    @commands.command(help="Oh no")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wasted(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/wasted", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"wasted.png"
        ))

    @commands.command(help="Not fun fact: my owner lives in a communist country")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def comrade(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/comrade", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"comrade.png"
        ))

    @commands.command(help="Respect")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def passed(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/passed", params={"avatar": member.display_avatar.url}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"passed.png"
        ))

    @commands.command(help="Make a fake youtube comment", aliases=["ytc"])
    async def ytcomment(self, ctx, *, comment="Nothing you idiot"):
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/youtube-comment", params={
                "avatar": ctx.author.display_avatar.url,
                "username": ctx.author.name,
                "comment": comment
            }
        )
        await ctx.send(file=discord.File(io.BytesIO(await resp.read()), 'yt.png'))

    @commands.command(help="Make a fake tweet")
    async def tweet(self, ctx, name, *, comment="Nothing you idiot"):
        resp = await self.bot.session.get(
            f"https://some-random-api.ml/canvas/tweet", params={
                "avatar": ctx.author.display_avatar.url,
                "username": ctx.author.name,
                "displayname": name,
                "comment": comment
            }
        )
        await ctx.send(file=discord.File(io.BytesIO(await resp.read()), 'tweet.png'))

    @commands.command(help="Surprised pikachu")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def pikachu(self, ctx, *, text="Nothing"):
        resp = await self.bot.session.get(
            f"https://api.popcat.xyz/pikachu", params={"text": text}
        )
        await ctx.send(file=discord.File(
            io.BytesIO(await resp.read()), f"pikachu.png"
        ))