from core.dangvietbot import DangVietBot
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
bcursor = cluster['bot']['blacklist']

bot = DangVietBot()


@bot.check
async def block_blacklist_user(ctx):
    return await bcursor.find_one({"id": ctx.author.id}) is None

bot.add_check(block_blacklist_user)

if __name__ == '__main__':
    # bot.ipc.start()
    bot.run()
