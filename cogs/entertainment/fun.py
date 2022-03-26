import discord
from discord.ext import commands
import json
import requests
import asyncpraw
import random
import asyncio
from utils.configs import config_var
import urllib
import aiohttp
import io


reddit = asyncpraw.Reddit(client_id="WS8DpWseFlxeec8_v2sjrw",
                          client_secret=config_var['reddit_secret'],
                          username='DangVietHoang',
                          password=config_var['reddit_pass'],
                          user_agent='')


def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = f"**{json_data[0]['q']}**\n          -{json_data[0]['a']}"
    return quote


all_sub = []


async def gen_meme():
    subreddit = await reddit.subreddit("memes")
    hot = subreddit.hot()
    async for submission in hot:
        all_sub.append(submission)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await gen_meme()

    @commands.command(aliases=["iqrate"], help="Accurately rate your IQ without taking a test")
    async def iq(self, ctx):
        iq = random.randint(0, 1000)
        await ctx.send(f"Your IQ score is {iq}")

    @commands.command(help="Returns a quote")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def quote(self, ctx):
        quotes = get_quote()
        await ctx.send(quotes)

    @commands.command(help="Fresh reddit memes")
    async def meme(self, ctx):
        # meme command base on dank memer, speed up asyncpraw code from https://stackoverflow.com/questions/67101891/discord-py-meme-command-takes-a-lot-of-time
        random_sub = random.choice(all_sub)
        all_sub.append(random_sub)

        name = random_sub.title
        url = random_sub.url
        upvote = random_sub.score
        comment = random_sub.num_comments
        link = random_sub.permalink

        embed = discord.Embed(title=f'{name}', color=discord.Color.orange(), url=f"https://reddit.com{link}")
        embed.set_image(url=url)
        embed.set_footer(text=f"👍 {upvote} | 💬 {comment}", icon_url='https://www.vectorico.com/download/social_media/Reddit-Icon.png')
        await ctx.send(embed=embed)

        if len(all_sub) <= 20:  # meme collection running out owo
            await gen_meme()

    @commands.command(help="Get dog facts")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def dogfact(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/facts/dog") as resp:
                data = await resp.json()
                await ctx.send(f"**Dog Fact:** {data['fact']}")

    @commands.command(help="Get cat facts")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def catfact(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/facts/cat") as resp:
                data = await resp.json()
                await ctx.send(f"**Cat Fact:** {data['fact']}")

    @commands.command(help="Get bird facts")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def birdfact(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/facts/bird") as resp:
                data = await resp.json()
                await ctx.send(f"**Bird Fact:** {data['fact']}")

    @commands.command(help="Measure your pp size", aliases=["cock", 'dong'])
    async def pp(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(embed=discord.Embed(title=f"{member} pp size", description=f"8{'='*random.randint(0, 50)}D", color=discord.Color.purple()))

    @commands.command(help="Emojify your text")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def emojify(self, ctx, *, text):
        # also base on dank memer
        emojis = []
        for s in text:
            if s.isdecimal():
                num2emo = {'0': 'zero', '1': 'one', '2': 'two',
                           '3': 'three', '4': 'four', '5': 'five',
                           '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
                emojis.append(f":{num2emo.get(s)}:")
            elif s.isalpha():
                emojis.append(f":regional_indicator_{s.lower()}:")
            else:
                emojis.append(s)
        await ctx.send(''.join(emojis))

    @commands.command(help="Show your gay pride")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://some-random-api.ml/canvas/gay?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'gay.png'))

    @commands.command(help="Get a horny permission's card")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def horny(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://some-random-api.ml/horny?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'horny.png'))

    @commands.command(help="U R arrested")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def jail(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://some-random-api.ml/canvas/jail?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'jail.png'))

    @commands.command(help="Funny shit")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def joke(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://some-random-api.ml/joke") as resp:
                data = await resp.json()
                await ctx.send(data['joke'])

    @commands.command(aliases=['pokeidex'], help="Show pokemon info")
    async def pokedex(self, ctx, *, pokemon):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://some-random-api.ml/pokedex?pokemon={urllib.parse.quote(pokemon)}") as resp:
                data = await resp.json()
        if data.get('error'):
            return await ctx.send(f"Received unexpected error: {data['error']}")
        embed = discord.Embed(title=data['name'], description=data['description'])
        embed.add_field(name="Generation", value=data['generation'])
        embed.add_field(name="Type", value=", ".join(poketype for poketype in data['type']))
        embed.add_field(name="Species", value=", ".join(species for species in data['species']))
        embed.add_field(name="Abilities", value=", ".join(abilities for abilities in data['abilities']))
        embed.add_field(name="Id", value=data['id'])
        embed.add_field(name="Height", value=data['height'])
        embed.add_field(name="Weight", value=data['weight'])
        embed.add_field(name="Gender", value=", ".join(gender for gender in data['gender']))
        embed.add_field(name="Base Experience", value=data['base_experience'])
        embed.add_field(name="Egg group", value=", ".join(egg_groups for egg_groups in data['egg_groups']))
        embed.add_field(name="HP", value=data['stats']['hp'])
        embed.add_field(name="Attack", value=data['stats']['attack'])
        embed.add_field(name="Defense", value=data['stats']['defense'])
        embed.add_field(name="Speed Attack", value=data['stats']['sp_def'])
        embed.add_field(name="Speed Defense", value=data['stats']['sp_def'])
        embed.add_field(name="Speed", value=data['stats']['speed'])
        embed.add_field(name="Total", value=data['stats']['total'])
        embed.set_thumbnail(url=data['sprites']['animated'])

    @commands.command(help="GET TRIGGERED")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def triggered(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://some-random-api.ml/canvas/triggered?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'triggered.gif'))

    @commands.command(help="Oh no")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def wasted(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://some-random-api.ml/canvas/wasted?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'wasted.png'))

    @commands.command(help="Not fun fact: my owner lives in a communist country")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def comrade(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://some-random-api.ml/canvas/comrade?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'comrade.png'))

    @commands.command(help="Respect")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def passed(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'https://some-random-api.ml/canvas/passed?avatar={member.display_avatar.url}') as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'wasted.png'))

    @commands.command(help="Make a fake youtube comment")
    async def ytcomment(self, ctx, *, comment="Nothing you idiot"):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://some-random-api.ml/canvas/youtube-comment?avatar={ctx.author.display_avatar.url}&username={ctx.author.name}&comment={urllib.parse.quote(comment)}") as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'yt.png'))

    @commands.command(help="Make a fake tweet")
    async def tweet(self, ctx, name="No Name", *, comment="Nothing you idiot"):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://some-random-api.ml/canvas/tweet?avatar={ctx.author.display_avatar.url}&displayname={name}&comment={urllib.parse.quote(comment)}&username={ctx.author.name}") as rsp:
                imageData = io.BytesIO(await rsp.read())
                await session.close()
                await ctx.send(file=discord.File(imageData, 'tweet.png'))

    @commands.command(name="8ball", help="ask anything")
    async def _8ball(self, ctx, *, question):
        answer = [
            'It is Certain.',
            'It is decidedly so',
            'Without a doubt.',
            'Yes definitely.',
            'You may rely on it',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good',
            'Yes',
            'Signs point to yes.',
            'Reply hazy, try again.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.',
            "Don't count on it.",
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good',
            'Very doubtful'
        ]
        await ctx.send(f"**Q:** {question}\n**A:** {random.choice(answer)}")

    @commands.command(help="Steal their data")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def hack(self, ctx, member: discord.Member = None):
        if member is None:
            await ctx.send("I don't see someone to hack, maybe later?")
        else:
            msg = await ctx.send("`$python hack.py`")
            await asyncio.sleep(2)
            msg2 = await msg.edit(content="Get user.id")
            await asyncio.sleep(2)
            msg3 = await msg2.edit(content="open users.bson")
            await asyncio.sleep(2)
            msg4 = await msg3.edit(content=f"Find user.id in line {random.randint(1, 350000000)}")
            await asyncio.sleep(2)
            msg5 = await msg4.edit(content=f"email: `{member.name}.gmail.com`\npassword: `********` \nip address: `1.2.7:500`")
            await asyncio.sleep(2)
            msg6 = await msg5.edit(content="Checking user activity")
            await asyncio.sleep(2)
            msg7 = await msg6.edit(content="Report to discord for violating TOS")
            await asyncio.sleep(2)
            msg8 = await msg7.edit(content="Report to the local government for breaking the law")
            await asyncio.sleep(2)
            await msg8.edit(content=f"Finish hacking {member}")