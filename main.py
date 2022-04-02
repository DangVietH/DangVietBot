from core.dangvietbot import DangVietBot
import asyncio
from utils.configs import config_var
from motor.motor_asyncio import AsyncIOMotorClient

bot = DangVietBot()


async def main():
    async with bot:
        bot.mongo = AsyncIOMotorClient(config_var['mango_link'])
        await bot.start(config_var['token'])

asyncio.run(main())