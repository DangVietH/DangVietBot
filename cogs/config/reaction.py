from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
from cogs.config.configuration import ConfigurationBase
import asyncio

cluster = AsyncIOMotorClient(config_var['mango_link'])
cursor = cluster["react_role"]['reaction_roles']


# code base on https://github.com/AdvicSaha443/Discord.py-Self-Role-Bot/blob/main/main.py


class Reaction(ConfigurationBase):
    @commands.group(invoke_without_command=True, case_insensitive=True, help="Reaction role setup")
    async def reaction(self, ctx):
        _cmd = self.bot.get_command("help")
        await _cmd(ctx, command='reaction')

    @reaction.command(help="Set up reaction role")
    @commands.has_permissions(manage_messages=True)
    async def create(self, ctx):
        await ctx.send("Answer These Question In Next 10Min!")

        questions = ["Enter Message: ", "Enter Emojis: ", "Enter Roles (only type role id): ", "Enter Channel: "]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)

            try:
                msg = await self.bot.wait_for('message', timeout=600.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Type Faster Next Time!")
                return
            else:
                answers.append(msg.content)

        emojis = answers[1].split(" ")
        roles = answers[2].split(" ")
        c_id = int(answers[3][2:-1])
        channel = self.bot.get_channel(c_id)

        bot_msg = await channel.send(answers[0])

        insert = {"id": bot_msg.id, "emojis": emojis, "roles": roles, "guild": ctx.guild.id}
        await cursor.insert_one(insert)
        for emoji in emojis:
            await bot_msg.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        else:
            check = await cursor.find_one({"id": payload.message_id})
            if check is not None:
                emojis = []
                roles = []

                for emoji in check['emojis']:
                    emojis.append(emoji)

                for role in check['roles']:
                    roles.append(role)

                guild = self.bot.get_guild(payload.guild_id)

                for i in range(len(emojis)):
                    chose_emoji = str(payload.emoji)
                    if chose_emoji == emojis[i]:
                        selected_role = roles[i]

                        role = guild.get_role(int(selected_role))

                        await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        check = await cursor.find_one({"id": payload.message_id})
        if check is not None:
            emojis = []
            roles = []

            for emoji in check['emojis']:
                emojis.append(emoji)

            for role in check['roles']:
                roles.append(role)

            guild = self.bot.get_guild(payload.guild_id)

            for i in range(len(emojis)):
                chose_emoji = str(payload.emoji)
                if chose_emoji == emojis[i]:
                    selected_role = roles[i]

                    role = guild.get_role(int(selected_role))
                    member = await(guild.fetch_member(payload.user_id))
                    if member is not None:
                        await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        check = await cursor.find_one({"id": payload.message_id})
        if check is not None:
            await cursor.delete_one(check)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await cursor.find_one({"guild": guild.id})
        if result is not None:
            await cursor.delete_one({"guild": guild.id})
