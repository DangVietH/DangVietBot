from core.dangvietbot import DangVietBot
import asyncio
from utils.configs import config_var
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

bot = DangVietBot()


async def main():
    async with aiohttp.ClientSession() as session:
        async with bot:
            bot.httpsession = session
            bot.mongo = AsyncIOMotorClient(config_var['mango_link'])
            await bot.start(config_var['token'])

asyncio.run(main())