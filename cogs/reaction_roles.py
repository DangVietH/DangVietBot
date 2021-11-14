import discord
import asyncio
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
import json

with open('config.json') as f:
    data = json.load(f)

cluster = AsyncIOMotorClient(data['mango_link'])
db = cluster["react_role"]
cursor = db['reaction_roles']

# code base on https://github.com/AdvicSaha443/Discord.py-Self-Role-Bot/blob/main/main.py


class Reaction(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(help="Set up reaction role")
    @commands.has_permissions(administrator=True)
    async def self_react(self, ctx):
        await ctx.send("Answer These Question In Next 10Min!")

        questions = ["Enter Message: ", "Enter Emojis: ", "Enter Roles: ", "Enter Channel: "]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)

            try:
                msg = await self.client.wait_for('message', timeout=600.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Type Faster Next Time!")
                return
            else:
                answers.append(msg.content)

        emojis = answers[1].split(" ")
        roles = answers[2].split(" ")
        c_id = int(answers[3][2:-1])
        channel = self.client.get_channel(c_id)

        bot_msg = await channel.send(answers[0])

        insert = {"id": bot_msg.id, "emojis": emojis, "roles": roles}
        await cursor.insert_one(insert)
        for emoji in emojis:
            await bot_msg.add_reaction(emoji)

    @commands.command(help="Delete reaction role system. This does not delete the message.")
    @commands.has_permissions(administrator=True)
    async def del_react(self, ctx, msg_id: int):
        check = await cursor.find_one({"id": msg_id})
        if msg_id == check['id']:
            await cursor.delete_one(check)
            await ctx.send("Success. Now go and delete the reaction message if you haven't")
        else:
            await ctx.send("Can't find that message id")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        else:
            check = await cursor.find_one({"id": payload.message_id})
            if payload.message_id == check['id']:
                emojis = []
                roles = []

                for emoji in check['emojis']:
                    emojis.append(emoji)

                for role in check['roles']:
                    roles.append(role)

                guild = self.client.get_guild(payload.guild_id)

                for i in range(len(emojis)):
                    chose_emoji = str(payload.emoji)
                    if chose_emoji == emojis[i]:
                        selected_role = roles[i]

                        role = discord.utils.get(guild.roles, name=selected_role)

                        await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        check = await cursor.find_one({"id": payload.message_id})
        if payload.message_id == check['id']:
            emojis = []
            roles = []

            for emoji in check['emojis']:
                emojis.append(emoji)

            for role in check['roles']:
                roles.append(role)

            guild = self.client.get_guild(payload.guild_id)

            for i in range(len(emojis)):
                chose_emoji = str(payload.emoji)
                if chose_emoji == emojis[i]:
                    selected_role = roles[i]

                    role = discord.utils.get(guild.roles, name=selected_role)
                    member = await(guild.fetch_member(payload.user_id))
                    if member is not None:
                        await member.remove_roles(role)


def setup(client):
    client.add_cog(Reaction(client))
