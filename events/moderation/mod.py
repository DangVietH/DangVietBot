import discord
from discord.ext import commands, tasks
import datetime


class ModEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(seconds=10)
    async def time_checker(self):
        try:
            all_timer = self.bot.mongo["timer"]['mod'].find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    if x['type'] == "ban":
                        server = self.bot.get_guild(int(x['guild']))
                        user = self.bot.get_user(int(x['user']))
                        await server.unban(user, reason="Time up!")

                        await self.bot.mongo["timer"]['mod'].delete_one(x)
                else:
                    pass
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        insert = {"guild": guild.id, "num": 0, "cases": [], "ban": []}
        await self.bot.mongo["moderation"]['cases'].insert_one(insert)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.mongo["moderation"]['cases'].delete_one({"guild": guild.id})
        if await self.bot.mongo["moderation"]['modlog'].find_one({"guild": guild.id}):
            await self.bot.mongo["moderation"]['modlog'].delete_one({"guild": guild.id})
        if await self.bot.mongo["moderation"]['modrole'].find_one({"guild": guild.id}):
            await self.bot.mongo["moderation"]['modrole'].delete_one({"guild": guild.id})
        for member in guild.members:
            if not member.bot:
                result = await self.bot.mongo["moderation"]['user'].find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await self.bot.mongo["moderation"]['user'].delete_one(result)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await self.bot.mongo["moderation"]['user'].find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await self.bot.mongo["moderation"]['user'].delete_one(result)