from discord.ext import commands


class EconEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.bot.mongo["economy"]["member"].insert_one({"guild": member.guild.id, "user": member.id, "wallet": 0, "bank": 0, "inventory": []})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if await self.bot.mongo["economy"]["member"].find_one({"guild": member.guild.id, "user": member.id}):
            await self.bot.mongo["economy"]["member"].delete_one({"guild": member.guild.id, "user": member.id})

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.mongo['economy']['server'].insert_one({
            'guild': guild.id,
            "daily": 1000,
            'shop': [],
            'econ_symbol': '$',
        })

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.mongo['economy']['server'].delete_one({
            'guild': guild.id
        })