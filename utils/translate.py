import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["bot"]["lang"]


class Translate:
    def tran(self, guild):
        data = await cursor.find_one({"guild": guild.id})

        langs = {
            "en": "English",
            "vn": "Vietnamese"
        }
