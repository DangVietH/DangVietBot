import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from main import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["bot"]["lang"]
