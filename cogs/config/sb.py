import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from utils.configs import config_var
from cogs.config.configuration import ConfigurationBase

# some code base on https://github.com/MenuDocs/Pyro/blob/master/cogs/starboard.py

cluster = AsyncIOMotorClient(config_var['mango_link'])

cursor = cluster['sb']['config']
msg_cursor = cluster['sb']['msg']


class Star(ConfigurationBase):
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

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Starboard stuff", aliases=['sb', 'star'])
    async def starboard(self, ctx):
        _cmd = self.bot.get_command("help")
        await _cmd(ctx, command='starboard')

    @starboard.command(help="Show starboard stats")
    async def stats(self, ctx):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        embed = discord.Embed(title="Starboard Stats", color=discord.Color.random())
        embed.add_field(name="Starboard Channel", value=f"{self.bot.get_channel(result['channel']).mention}")
        embed.add_field(name="Starboard Emojis", value=f"{result['emoji']}")
        embed.add_field(name="Starboard Threshold", value=f"{result['threshold']}")
        embed.add_field(name="Starboard Message Expire", value=f"{result['age']} seconds")
        embed.add_field(name="Starboard Ignored Channels",
                        value=f"{[self.bot.get_channel(channel).mention for channel in result['ignoreChannel']]}")
        await ctx.send(embed=embed)

    @starboard.command(help="Setup starboard channel")
    @commands.has_permissions(manage_channels=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            await cursor.insert_one({
                "guild": ctx.guild.id,
                "channel": channel.id,
                "emoji": "⭐",
                "threshold": 2,
                "ignoreChannel": [],
                "lock": False,
                "selfStar": False
            })
            await ctx.send(f"Starboard channel set to {channel.mention}")
            return
        await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
        await ctx.send(f"Starboard channel updated to {channel.mention}")

    @starboard.command(help="Toggle self star")
    @commands.has_permissions(manage_guild=True)
    async def selfStar(self, ctx):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        if result['selfStar'] is True:
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"selfStar": False}})
            await ctx.send("Selfstar is now off")
        else:
            await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"selfStar": True}})
            await ctx.send("Selfstar is now on")

    @starboard.command(help="Ignore channels from starboard")
    @commands.has_permissions(manage_channels=True)
    async def ignoreChannel(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        for c in channel:
            if c in result['ignoreChannel']:
                continue
            await cursor.update_one({"guild": ctx.guild.id}, {"$push": {"ignoreChannel": c.id}})
        await ctx.send(f"Ignored channels {[x.mention for x in channel]}")

    @starboard.command(help="Un ignore channels from starboard")
    @commands.has_permissions(manage_channels=True)
    async def unignoreChannel(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        result = await cursor.find_one({"guild": ctx.guild.id})
        if result is None:
            return await ctx.send("You don't have a starboard system")
        for c in channel:
            if c in result['ignoreChannel']:
                continue
            await cursor.update_one({"guild": ctx.guild.id}, {"$pull": {"ignoreChannel": c.id}})
        await ctx.send(f"Unignored channels {[x.mention for x in channel]}")

    @starboard.command(help="Set starboard emoji amount", aliases=["amount"])
    @commands.has_permissions(manage_guild=True)
    async def threshold(self, ctx, threshold: int):
        if await cursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"threshold": threshold}})
        await ctx.send(f"Starboard threshold updated to {threshold}")

    @starboard.command(help="Lock starboard")
    @commands.has_permissions(manage_guild=True)
    async def lock(self, ctx):
        if await cursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"lock": True}})
        await ctx.send("Starboard locked")

    @starboard.command(help="Lock starboard")
    @commands.has_permissions(manage_guild=True)
    async def unlock(self, ctx):
        if await cursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await cursor.update_one({"guild": ctx.guild.id}, {"$set": {"lock": False}})
        await ctx.send("Starboard unlocked")

    @starboard.command(help="Disable starboard system")
    @commands.has_permissions(manage_channels=True)
    async def disable(self, ctx):
        if await cursor.find_one({"guild": ctx.guild.id}) is None:
            return await ctx.send("You don't have a starboard system")
        await cursor.delete_one({"guild": ctx.guild.id})
        await ctx.send("Starboard system disabled")

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
                if msg.author.id in react and guildstats['selfStar'] is False:
                    react.pop(react.index(msg.author.id))
                if len(react) >= guildstats['threshold']:
                    msgstats = await msg_cursor.find_one({'message': payload.message_id})

                    if msgstats is None:
                        starmsg = await star_channel.send(f"{emoji} **{len(react)} |** {channel.mention}", embed=self.embedGenerator(msg))
                        await msg_cursor.insert_one({'message': payload.message_id, 'star_msg': starmsg.id, 'amount': len(react), 'guild': payload.guild_id, 'channel': payload.channel_id})
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
                msgstats = await msg_cursor.find_one({'message': payload.message_id})
                if msgstats is not None:
                    starmsg = await star_channel.fetch_message(msgstats['star_msg'])
                    if not react or len(react) >= guildstats['threshold']:
                        await starmsg.edit(f"{emoji} **{len(react)} |** {channel.mention}", embed=self.embedGenerator(msg))
                        await msg_cursor.update_one({'message': payload.message_id}, {'$inc': {'amount': -1}})
                    else:
                        await msg_cursor.delete_one({"message": payload.message_id})
                        await starmsg.delete()

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        check = await msg_cursor.find_one({"message": after.id})
        if check is not None:
            guildstats = await cursor.find_one({'guild': after.guild.id})
            star_channel = self.bot.get_channel(guildstats['channel'])
            starmsg = await star_channel.fetch_message(check['star_msg'])
            await starmsg.edit(f"{guildstats['emoji']} **{check['amount']} |** {self.bot.get_channel(check['channel']).mention}", embed=self.embedGenerator(after))

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