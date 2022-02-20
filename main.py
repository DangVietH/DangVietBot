import os
from core.bot import DHB
from motor.motor_asyncio import AsyncIOMotorClient

config_var = {
    "token": os.environ.get("token"),
    "mango_link": os.environ.get("mango_link"),
    "reddit_pass": os.environ.get("reddit_pass"),
    "reddit_secret": os.environ.get("reddit_secret")
}

cluster = AsyncIOMotorClient(config_var['mango_link'])
bcursor = cluster['bot']['blacklist']

bot = DHB()


@bot.check
async def block_blacklist_user(ctx):
    return await bcursor.find_one({"id": ctx.author.id}) is None

bot.add_check(block_blacklist_user)

if __name__ == '__main__':
    bot.run()
