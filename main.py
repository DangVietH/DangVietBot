from core.dangvietbot import DangVietBot
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

bot = DangVietBot()

cluster = AsyncIOMotorClient(config_var['mango_link'])

blacklist = cluster['bot']['blacklist']


@bot.check
async def block_blacklist_user(ctx):
    return await blacklist.find_one({"id": ctx.author.id}) is None


if __name__ == '__main__':
    bot.run()