from discord.ext import commands


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if await self.bot.mongo["levelling"]['disable'].find_one({"guild": message.guild.id}):
            return
        if await self.bot.mongo['bot']['blacklist'].find_one({"id": message.author.id}):
            return

        stats = await self.bot.mongo["levelling"]['member'].find_one(
            {'guild': message.guild.id, "user": message.author.id})
        if stats is None:
            await self.bot.mongo["levelling"]['member'].insert_one(
                {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 5})
            return

        lconf = await self.bot.mongo["levelling"]['roles'].find_one({"guild": message.guild.id})

        if message.channel.id in lconf['ignoreChannel']:
            return
        for r in message.author.roles:
            if r.id in lconf['ignoreRole']:
                return

        await self.bot.mongo["levelling"]['member'].update_one(
            {"guild": message.guild.id, "user": message.author.id},
            {"$inc": {"xp": int(lconf['xp'])}})

        xp = stats['xp']
        lvl = 0
        while True:
            if xp < ((100 / 2 * (lvl ** 2)) + (100 / 2 * lvl)):
                break
            lvl += 1

        xp -= ((100 / 2 * ((lvl - 1) ** 2)) + (100 / 2 * (lvl - 1)))
        if stats["xp"] < 0:
            self.bot.mongo["levelling"]['member'].update_one({"guild": message.guild.id, "user": message.author.id},
                                                             {"$set": {"xp": 0}})
        if stats['level'] < lvl:
            await self.bot.mongo["levelling"]['member'].update_one(
                {"guild": message.guild.id, "user": message.author.id},
                {"$inc": {"level": 1}})

            lvl_channel = await self.bot.mongo["levelling"]['channel'].find_one({"guild": message.guild.id})
            if lvl_channel is None:
                await message.channel.send(lconf['msg'].format(
                    mention=message.author.mention,
                    name=message.author.name,
                    server=message.guild.name,
                    username=message.author,
                    level=stats['level'] + 1
                ))
            else:
                channel = self.bot.get_channel(lvl_channel["channel"])
                await channel.send(lconf['msg'].format(
                    mention=message.author.mention,
                    name=message.author.name,
                    server=message.guild.name,
                    username=message.author,
                    level=stats['level'] + 1
                ))

            levelrole = lconf['role']
            levelnum = lconf['level']
            for i in range(len(levelrole)):
                if lvl == int(levelnum[i]):
                    role = message.guild.get_role(int(levelrole[i]))
                    await message.author.add_roles(role)
                    lvl_channel = await self.bot.mongo["levelling"]['channel'].find_one({"guild": message.guild.id})
                    if lvl_channel is None:
                        return await message.channel.send(
                            f"{message.author}also receive {role.name} role")
                    channel = self.bot.get_channel(lvl_channel["channel"])
                    await channel.send(f"🎉 {message.author} also receive {role.name} role")
