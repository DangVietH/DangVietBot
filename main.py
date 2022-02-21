import os
from core.dangvietbot import DangVietBot
from motor.motor_asyncio import AsyncIOMotorClient

config_var = {
    "mango_link": os.environ.get("mango_link"),
    "reddit_pass": os.environ.get("reddit_pass"),
    "reddit_secret": os.environ.get("reddit_secret")
}

cluster = AsyncIOMotorClient(config_var['mango_link'])
bcursor = cluster['bot']['blacklist']

bot = DangVietBot()


@bot.check
async def block_blacklist_user(ctx):
    return await bcursor.find_one({"id": ctx.author.id}) is None

bot.add_check(block_blacklist_user)

if __name__ == '__main__':
    bot.run()
