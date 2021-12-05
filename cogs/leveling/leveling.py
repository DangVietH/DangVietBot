import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["levelling"]
levelling = db['member']
disable = db['disable']
role = db['roles']
upchannel = db['channel']

# pagination code bade on https://github.com/KumosLab/Discord-Economy-Bot/blob/main/Commands/leaderboard.py


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild:
            if not message.author.bot:
                is_disabled = await disable.find_one({"guild": message.guild.id})
                if is_disabled is None:
                    stats = await levelling.find_one({'guild': message.guild.id, "user": message.author.id})
                    if stats is None:
                        insert = {'guild': message.guild.id, "user": message.author.id, 'level': 0, 'xp': 5}
                        await levelling.insert_one(insert)
                    else:
                        add_exp = stats['xp'] + 5
                        await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                                   {"$set": {"xp": add_exp}})
                        lvl_start = stats['level']
                        lvl_end = int(stats['xp'] ** (1 / 4))
                        if lvl_start < lvl_end:
                            new_lvl = lvl_start + 1
                            await levelling.update_one({"guild": message.guild.id, "user": message.author.id},
                                                       {"$set": {"level": new_lvl}})
                            lvl_channel = await upchannel.find_one({"guild": message.guild.id})
                            if lvl_channel is None:
                                await message.channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")
                            else:
                                channel = self.bot.get_channel(lvl_channel["channel"])
                                await channel.send(f"🎉 {message.author.mention} has reach level **{new_lvl}**!!🎉")
                else:
                    return None

    @commands.command(help="Disable levelling")
    @commands.has_permissions(administrator=True)
    async def disable_level(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await ctx.send("Bruh")
        else:
            insert = {"guild": ctx.guild.id}
            await disable.insert_one(insert)
            for member in ctx.guild.members:
                if not member.bot:
                    result = await levelling.find_one({"guild": ctx.guild.id, "user": member.id})
                    if result is not None:
                        await levelling.delete_one({"guild": ctx.guild.id, "user": member.id})
            await ctx.send('Levelling disabled')

    @commands.command(help="Re-enable levelling")
    @commands.has_permissions(administrator=True)
    async def renable_level(self, ctx):
        check = await disable.find_one({"guild": ctx.guild.id})
        if check is not None:
            await disable.delete_one(check)
            await ctx.send('Levelling re-enable')
        else:
            await ctx.send('Leveling already enabled')

    @commands.command(help="See your rank")
    async def rank(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        stats = await levelling.find_one({'guild': ctx.guild.id, "user": user.id})
        if stats is not None:
            ranking = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
            rank = 0
            async for x in ranking:
                rank += 1
                if stats['user'] == x['user']:
                    break

            embed = discord.Embed(title=user, color=user.color)
            embed.add_field(name="Level", value=f"#{stats['level']}")
            embed.add_field(name="XP", value=f"#{stats['xp']}/{stats['xp'] ** 1/4}")
            embed.add_field(name="Rank", value=f"#{rank}")
            embed.set_thumbnail(url=user.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The specified member haven't send a message in this server!!")

    @commands.command(help="See server ranks")
    async def top(self, ctx):
        stats = levelling.find({'guild': ctx.guild.id}).sort("xp", -1)
        embed = discord.Embed(title=f"🏆 Leaderboard of {ctx.guild.name}", color=discord.Color.random())
        user = []
        lvl = []
        xp = []
        async for x in stats:
            user.append(x['user'])
            lvl.append(x['level'])
            xp.append(x['xp'])

        pagination = list(zip(user, lvl, xp))
        pages = [pagination[i:i + 10] for i in range(0, len(pagination), 10)]
        page = 0
        num = 0
        user_list = []
        lvl_list = []
        xp_list = []
        for i in pages:
            embed.clear_fields()
            for users, lvl, xp in i:
                num += 1
                him = ctx.guild.get_member(users)
                embed.add_field(name=f"{num}: {him}", value=f"**Level:** {lvl}  **XP:** {xp}", inline=False)
            embed.set_footer(text=f"Page {page + 1}/{len(pages)}")
            message = await ctx.send(embed=embed)
            page += 1
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            while True:
                def check(reaction, userz):
                    return userz == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "⬅️":
                        if page == 1:
                            await message.remove_reaction("⬅️", user)
                        else:
                            page -= 1
                            embed.clear_fields()
                            for users, lvl, xp in pages[page - 1]:
                                num -= 1
                                user_list.append(users)
                                lvl_list.append(lvl)
                                xp_list.append(xp)
                            for x in range(0, 10):
                                him = ctx.guild.get_member(user_list[x])
                                embed.add_field(name=f"{x + 1 + num - len(user_list)}: {him}", value=f"**Level:** {lvl_list[x]}  **XP:** {xp_list[x]}", inline=False)
                            user_list.clear()
                            lvl_list.clear()
                            xp_list.clear()
                            embed.set_footer(text=f"Page {page}/{len(pages)}")
                            await message.edit(embed=embed)
                            await message.remove_reaction("⬅️", user)
                            await message.remove_reaction("➡️", user)

                    elif str(reaction.emoji) == "➡️":
                        if page == len(pages):
                            await message.remove_reaction("➡️", user)
                        else:
                            page += 1
                            embed.clear_fields()
                            for users, lvl, xp in pages[page - 1]:
                                num += 1
                                user_list.append(users)
                                lvl_list.append(lvl)
                                xp_list.append(xp)
                                him = ctx.guild.get_member(users)
                                embed.add_field(name=f"{num}: {him}",
                                                value=f"**Level:** {lvl}  **XP:** {xp}", inline=False)
                            if len(user_list) != 10:
                                get_ten = 10 - len(user_list)
                                num += get_ten
                            user_list.clear()
                            lvl_list.clear()
                            xp_list.clear()
                            embed.set_footer(text=f"Page {page}/{len(pages)}")
                            await message.edit(embed=embed)
                            await message.remove_reaction("⬅️", user)
                            await message.remove_reaction("➡️", user)

                except asyncio.TimeoutError:
                    await message.clear_reaction("⬅️")
                    await message.clear_reaction("➡️")

    @commands.command(help="See global rank")
    async def gtop(self, ctx):
        stats = levelling.find().sort("xp", -1)
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(icon_url="https://cdn.discordapp.com/attachments/900197917170737152/916598584005238794/world.png", name="Global Leaderboard")
        user = []
        lvl = []
        xp = []
        guild = []
        async for x in stats:
            user.append(x['user'])
            lvl.append(x['level'])
            xp.append(x['xp'])
            guild.append(x['guild'])

        pagination = list(zip(user, lvl, xp, guild))
        pages = [pagination[i:i + 10] for i in range(0, len(pagination), 10)]
        page = 0
        num = 0
        user_list = []
        lvl_list = []
        xp_list = []
        guild_list = []
        for i in pages:
            embed.clear_fields()
            for users, lvl, xp, guild in i:
                num += 1
                server = self.bot.get_guild(guild)
                embed.add_field(name=f"{num}: {self.bot.get_user(users)}", value=f"**Server:** {server}  **Level:** {lvl}  **XP:** {xp}", inline=False)
            embed.set_footer(text=f"Page {page + 1}/{len(pages)}")
            message = await ctx.send(embed=embed)
            page += 1
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            while True:
                def check(reaction, userz):
                    return userz == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "⬅️":
                        if page == 1:
                            await message.remove_reaction("⬅️", user)
                        else:
                            page -= 1
                            embed.clear_fields()
                            for users, lvl, xp, guild in pages[page - 1]:
                                num -= 1
                                user_list.append(users)
                                lvl_list.append(lvl)
                                xp_list.append(xp)
                                guild_list.append(guild)
                            for x in range(0, 10):
                                embed.add_field(name=f"{x + 1 + num - len(user_list)}: {self.bot.get_user(user_list[x])}",
                                                value=f"**Server:** {self.bot.get_guild(guild_list[x])} **Level:** {lvl_list[x]}  **XP:** {xp_list[x]}", inline=False)
                            user_list.clear()
                            lvl_list.clear()
                            xp_list.clear()
                            guild_list.clear()
                            embed.set_footer(text=f"Page {page}/{len(pages)}")
                            await message.edit(embed=embed)
                            await message.remove_reaction("⬅️", user)
                            await message.remove_reaction("➡️", user)

                    elif str(reaction.emoji) == "➡️":
                        if page == len(pages):
                            await message.remove_reaction("➡️", user)
                        else:
                            page += 1
                            embed.clear_fields()
                            for users, lvl, xp, guild in pages[page - 1]:
                                num += 1
                                user_list.append(users)
                                lvl_list.append(lvl)
                                xp_list.append(xp)
                                guild_list.append(guild)
                                embed.add_field(name=f"{num}: {self.bot.get_user(users)}",
                                                value=f"**Server:** {self.bot.get_guild(guild)} **Level:** {lvl}  **XP:** {xp}", inline=False)
                            if len(user_list) != 10:
                                get_ten = 10 - len(user_list)
                                num += get_ten
                            user_list.clear()
                            lvl_list.clear()
                            xp_list.clear()
                            guild_list.clear()
                            embed.set_footer(text=f"Page {page}/{len(pages)}")
                            await message.edit(embed=embed)
                            await message.remove_reaction("⬅️", user)
                            await message.remove_reaction("➡️", user)

                except asyncio.TimeoutError:
                    await message.clear_reaction("⬅️")
                    await message.clear_reaction("➡️")

    @commands.command(help="Setup level up channel if you like to")
    @commands.has_permissions(administrator=True)
    async def lvl_channel(self, ctx, channel: discord.TextChannel):
        result = await upchannel.find_one({"guild": ctx.guild.id})
        if result is None:
            insert = {"guild": ctx.guild.id, "channel": channel.id}
            await upchannel.insert_one(insert)
            await ctx.send(f"Level up channel set to {channel.mention}")
        elif result is not None:
            await upchannel.update_one({"guild": ctx.guild.id}, {"$set": {"channel": channel.id}})
            await ctx.send(f"Level up channel updated to {channel.mention}")

    # remove data to save storage
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                result = await levelling.find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await levelling.delete_one({"guild": guild.id, "user": member.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await levelling.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await levelling.delete_one({"guild": member.guild.id, "user": member.id})