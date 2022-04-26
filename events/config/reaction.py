from discord.ext import commands


# code base on https://github.com/AdvicSaha443/Discord.py-Self-Role-Bot/blob/main/main.py, which is unlicensed


class Reaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return
        check = await self.bot.mongo["react_role"]['reaction_roles'].find_one({"id": payload.message_id})
        if check:
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
        check = await self.bot.mongo["react_role"]['reaction_roles'].find_one({"id": payload.message_id})
        if check:
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
        check = await self.bot.mongo["react_role"]['reaction_roles'].find_one({"id": payload.message_id})
        if check is not None:
            await self.bot.mongo["react_role"]['reaction_roles'].delete_one(check)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        result = await self.bot.mongo["react_role"]['reaction_roles'].find_one({"guild": guild.id})
        if result is not None:
            await self.bot.mongo["react_role"]['reaction_roles'].delete_one({"guild": guild.id})
