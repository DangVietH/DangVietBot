from core import DangVietBot
import asyncio
from utils import config_var
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp

bot = DangVietBot()

mongo_connection = f"mongodb+srv://dhbbruh:{config_var['mongo_pass']}@dhb.tabp2.mongodb.net/welcome?retryWrites=true&w=majority"


async def main():
    async with aiohttp.ClientSession() as session:
        async with bot:
            bot.session = session
            bot.mongo = AsyncIOMotorClient(mongo_connection)
            await bot.start(config_var['token'])

asyncio.run(main())