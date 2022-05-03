import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import random


def convert(time):
    pos = ['s', 'm', 'h', 'd']

    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24}

    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2

    return val * time_dict[unit]


class Giveaway(commands.Cog):
    emoji = "🎉"

    def __init__(self, bot):
        self.bot = bot
        self.time_checker.start()

    async def cog_unload(self):
        self.time_checker.cancel()

    @commands.command(help="start Giveaway")
    @commands.has_permissions(manage_guild=True)
    async def gstart(self, ctx):
        giveaway_questions = ['Which channel will I host the giveaway in?', 'What is the prize?',
                              'How long should the giveaway run for (ex: 3h, 1d)?']
        giveaway_answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for question in giveaway_questions:
            await ctx.send(question)
            try:
                message = await self.bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(
                    "You didn't answer in time.  Please try again and be sure to send your answer within a minute of the question.")
                return
            else:
                giveaway_answers.append(message.content)

        try:
            c_id = int(giveaway_answers[0][2:-1])
        except ValueError:
            await ctx.send(f'Wizard crash because you failed to mention the channel correctly.  Please do it like this: {ctx.channel.mention}')
            return

        channel = self.bot.get_channel(c_id)
        prize = str(giveaway_answers[1])
        time = giveaway_answers[2]

        converted_time = convert(time)
        if converted_time == -1:
            return await ctx.send("You didn't answer the time correctly")

        if converted_time == -2:
            return await ctx.send("Time must be an integer")

        # message
        await ctx.send(
            f'The giveaway for {prize} will begin shortly.\nPlease direct your attention to {channel.mention}, this giveaway will end in {time} seconds.')

        end = datetime.datetime.utcnow() + datetime.timedelta(seconds=converted_time)
        give = discord.Embed(color=discord.Color.green(), title="🎉 GIVEAWAY TIME! 🎉", timestamp=end)
        give.add_field(name=f'{ctx.author.name} is giving away: {prize}!',
                       value=f'React with 🎁 to enter!\n Ends in <t:{int(datetime.datetime.timestamp(end))}:R> minutes!',
                       inline=False)

        give.set_footer(text=f'Giveaway ends at :')
        message = await channel.send(embed=give)
        await message.add_reaction("🎁")

        current_time = datetime.datetime.now()
        final_time = current_time + datetime.timedelta(seconds=converted_time)
        await self.bot.mongo["timer"]["giveaway"].insert_one({'message_id': message.id, 'time': final_time, "channel": channel.id, "prize": prize})

    @commands.command(help="Reroll the giveaway")
    @commands.has_permissions(manage_guild=True)
    async def gend(self, ctx, msg_id):
        if await self.bot.mongo["timer"]["giveaway"].find_one({'message_id': msg_id}) is None:
            return await ctx.send("Invalid Message ID.")
        await self.bot.mongo["timer"]["giveaway"].delete_one({'message_id': msg_id})
        gmsg = await ctx.fetch_message(msg_id)
        users = [user async for user in gmsg.reactions[0].users()]
        users.pop(users.index(self.bot.user))
        winner = random.choice(users)
        if len(users) < 1:
            return await gmsg.edit(embed=discord.Embed(color=discord.Color.red(), title="Nobody has entered the giveaway."))
        embed = discord.Embed(color=discord.Color.red(), title="🥳 THE GIVEAWAY HAS ENDED!",
                              description=f'🥳 **Winner**: {winner.mention}\n 🎫 **Number of Entrants**: {len(users)}')
        embed.set_footer(text='Thanks for entering the giveaway!')
        await gmsg.edit(embed=embed)

    @commands.command(help="Reroll the giveaway")
    @commands.has_permissions(manage_guild=True)
    async def greroll(self, ctx, msg_id):
        reroll_msg = await ctx.fetch_message(msg_id)
        if reroll_msg.author.id != self.bot.user.id:
            return await ctx.send("Invalid Message ID.")
        users = [user async for user in reroll_msg.reactions[0].users()]
        users.pop(users.index(self.bot.user))
        winner = random.choice(users)
        embed = discord.Embed(color=discord.Color.red(), title="🥳 New Winner of the giveaway! 🥳", description=f'🥳 **Winner**: {winner.mention}\n 🎫 **Number of Entrants**: {len(users)}')
        embed.set_footer(text='Thanks for entering the giveaway!')
        await reroll_msg.edit(embed=embed)

    @tasks.loop(seconds=10)
    async def time_checker(self):
        try:
            all_timer = self.bot.mongo["timer"]["giveaway"].find({})
            current_time = datetime.datetime.now()
            async for x in all_timer:
                if current_time >= x['time']:
                    msg_id = x['message_id']
                    channel = self.bot.get_channel(x['channel'])
                    msg = await self.bot.fetch_message(msg_id)
                    users = [user async for user in msg.reactions[0].users()]
                    users.pop(users.index(self.bot.user))

                    winner = random.choice(users)
                    if len(users) < 1:
                        await channel.send("No one has entered the giveaway. Maybe next time")
                        await self.bot.mongo["timer"]["giveaway"].delete_one({'message_id': msg_id})
                        return
                    embed = discord.Embed(color=discord.Color.red(), title="🥳 THE GIVEAWAY HAS ENDED!")
                    embed.add_field(name=f"🎉 Prize: {x['prize']}",
                                    value=f'🥳 **Winner**: {winner.mention}\n 🎫 **Number of Entrants**: {len(users)}',
                                    inline=False)
                    embed.set_footer(text='Thanks for entering the giveaway!')
                    await msg.edit(embed=embed)
                    await self.bot.mongo["timer"]["giveaway"].delete_one(x)

        except Exception as e:
            print(e)
