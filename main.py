from core import DangVietBot
import asyncio
from utils import config_var
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp

bot = DangVietBot()


async def main():
    async with aiohttp.ClientSession() as session:
        async with bot:
            bot.session = session
            bot.mongo = AsyncIOMotorClient(config_var['mango_link'])
            await bot.start(config_var['token'])

asyncio.run(main())