from core.dangvietbot import DangVietBot
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
bcursor = cluster['bot']['blacklist']

bot = DangVietBot()

if __name__ == '__main__':
    bot.run()