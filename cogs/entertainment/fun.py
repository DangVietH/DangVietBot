import nextcord as discord
from nextcord.ext import commands
import json
import requests
import asyncpraw
import random
import asyncio
from utils.configs import config_var


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

        embed = discord.Embed(title=f'__{name}__', color=discord.Color.purple(), url=f"https://reddit.com{link}")
        embed.set_image(url=url)
        embed.set_footer(text=f"⬆️ {upvote} | 💬 {comment}", icon_url='https://www.vectorico.com/download/social_media/Reddit-Icon.png')
        await ctx.send(embed=embed)

        if len(all_sub) <= 20:  # meme collection running out owo
            await gen_meme()

    @commands.command(help="Slap someone")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def slap(self, ctx, member: discord.Member = None):
        if member is None:
            await ctx.send("Please type the member name")
        else:
            await ctx.send(f"{ctx.author.mention} force DHB to slap {member.mention}")

    @commands.command(help="Measure your pp size", aliases=["cock", 'dong'])
    async def pp(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        pp = random.randint(0, 50)
        the_thing = "="
        await ctx.send(embed=discord.Embed(title=f"{member} pp size", description=f"8{the_thing*pp}D", color=discord.Color.purple()))

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
        await ctx.send(f"🎱 {random.choice(answer)}")

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