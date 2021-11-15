import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import os


cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["react_role"]
cursor = db['reaction_roles']

# code base on https://github.com/AdvicSaha443/Discord.py-Self-Role-Bot/blob/main/main.py


class Reaction(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(help="Set up reaction role")
    @commands.is_owner()
    async def react_role(self, ctx, emoji, msg_id, role: discord.Role):
        msg = await ctx.fetch_message(msg_id)
        insert = {"id": msg.id, "emoji": emoji, "role": role.id}
        await cursor.insert_one(insert)
        await msg.add_reaction(emoji)

    @commands.command(help="Delete reaction role system")
    @commands.is_owner()
    async def del_react(self, ctx, msg_id: int):
        check = await cursor.find_one({"id": msg_id})
        if msg_id == check['id']:
            await cursor.delete_one(check)
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("Can't find that message id")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        else:
            check = await cursor.find_one({"id": payload.message_id})
            if payload.message_id == check['id'] and payload.emoji.name == check['emoji']:
                role = payload.guild.get_role(check['role'])
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        check = await cursor.find_one({"id": payload.message_id})
        if payload.message_id == check['id'] and payload.emoji.name == check['emoji']:
            role = payload.guild.get_role(check['role'])
            await payload.member.remove_roles(role)


def setup(client):
    client.add_cog(Reaction(client))
