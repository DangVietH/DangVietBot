import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var

# some code base on https://github.com/MenuDocs/Pyro/blob/master/cogs/starboard.py

cluster = AsyncIOMotorClient(config_var['mango_link'])

cursor = cluster['sb']['config']
msg_cursor = cluster['sb']['msg']


class Star(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embedGenerator(self, msg):
        embed = discord.Embed(color=discord.Color.yellow(), timestamp=msg.created_at)
        embed.set_author(name=f"{msg.author}", icon_url=msg.author.display_avatar.url)
        embed.add_field(name="Source", value=f"[Jump]({msg.jump_url})")
        embed.set_footer(text=f"ID: {msg.id}")

        if msg.content:
            embed.description = msg.content

        attach = msg.attachments[0] if msg.attachments else None
        if attach:
            embed.set_image(url=attach.url)
        if msg.embeds:
            image = msg.embeds[0].image.url
            if image:
                embed.set_image(url=image)
        return embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.bot.get_guild(payload.guild_id):
            return

        guildstats = await cursor.find_one({'guild': payload.guild_id})
        if not guildstats:
            return

        star_channel = self.bot.get_channel(guildstats['channel'])
        channel = self.bot.get_channel(payload.channel_id)
        emoji = guildstats['emoji']
        if str(payload.emoji) == emoji:
            if guildstats['lock'] is True:
                return
            if channel.id == star_channel.id:
                return
            if channel.id in guildstats['ignoreChannel']:
                return
            msg = await channel.fetch_message(payload.message_id)
            reacts = list(filter(lambda r: str(r.emoji) == emoji, msg.reactions))
            if reacts:
                react = [user async for user in msg.reactions[0].users()]
                if msg.author.id in react:
                    react.pop(react.index(msg.author.id))
                if len(react) >= guildstats['threshold']:
                    msgstats = await msg_cursor.find_one({'message': payload.message_id})

                    if msgstats is None:
                        starmsg = await star_channel.send(f"{emoji} **{len(react)} |** {channel.mention}", embed=self.embedGenerator(msg))
                        await msg_cursor.insert_one({'message': payload.message_id, 'star_msg': starmsg.id, 'amount': len(react), 'guild': payload.guild_id})
                    else:
                        starbordMessage = await star_channel.fetch_message(msgstats['star_msg'])
                        await starbordMessage.edit(f"{emoji} **{len(react)} |** {channel.mention}", embed=self.embedGenerator(msg))
                        await msg_cursor.update_one({'message': payload.message_id}, {'$inc': {'amount': 1}})

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not self.bot.get_guild(payload.guild_id):
            return

        guildstats = await cursor.find_one({'guild': payload.guild_id})
        if not guildstats:
            return

        star_channel = self.bot.get_channel(guildstats['channel'])
        channel = self.bot.get_channel(payload.channel_id)
        emoji = guildstats['emoji']
        if str(payload.emoji) == emoji:
            if channel.id == star_channel.id:
                return
            msg = await channel.fetch_message(payload.message_id)
            reacts = list(filter(lambda r: str(r.emoji) == emoji, msg.reactions))
            if reacts:
                react = [user async for user in msg.reactions[0].users()]
                if msg.author.id in react:
                    react.pop(react.index(msg.author.id))
                msgstats = await msg_cursor.find_one({'message': payload.message_id})
                if msgstats is not None:
                    starmsg = await star_channel.fetch_message(msgstats['star_msg'])
                    if len(react) >= guildstats['threshold']:
                        await starmsg.edit(f"{emoji} **{len(react)} |** {channel.mention}", embed=self.embedGenerator(msg))
                        await msg_cursor.update_one({'message': payload.message_id}, {'$inc': {'amount': -1}})
                    else:
                        await msg_cursor.delete_one({"message": payload.message_id})
                        await starmsg.delete()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        check = await msg_cursor.find_one({"message": payload.message_id})
        if check is not None:
            await msg_cursor.delete_one(check)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if await cursor.find_one({"guild": guild.id}) and await msg_cursor.find_one({'guild': guild.id}) is not None:
            await cursor.delete_one({"guild": guild.id})
            await msg_cursor.delete_one({'guild': guild.id})