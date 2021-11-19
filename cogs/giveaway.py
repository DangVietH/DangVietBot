import discord
from discord.ext import commands
import datetime
import asyncio
import random


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="start Giveaway")
    @commands.has_permissions(administrator=True)
    async def giveaway(self, ctx):
        giveaway_questions = ['Which channel will I host the giveaway in?', 'What is the prize?',
                              'How long should the giveaway run for (in seconds)?', ]
        giveaway_answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for question in giveaway_questions:
            await ctx.send(question)
            try:
                message = await self.bot.wait_for('message', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(
                    "You didn't answer in time.  Please try again and be sure to send your answer within 30 seconds of the question.")
                return
            else:
                giveaway_answers.append(message.content)

        try:
            c_id = int(giveaway_answers[0][2:-1])
        except:
            await ctx.send(
                f'You failed to mention the channel correctly.  Please do it like this: {ctx.channel.mention}')
            return

        channel = self.bot.get_channel(c_id)
        prize = str(giveaway_answers[1])
        time = int(giveaway_answers[2])

        # message
        await ctx.send(
            f'The giveaway for {prize} will begin shortly.\nPlease direct your attention to {channel.mention}, this giveaway will end in {time} seconds.')

        give = discord.Embed(color=discord.Color.green())
        give.set_author(name=f'GIVEAWAY TIME!', icon_url='https://i.imgur.com/VaX0pfM.png')
        give.add_field(name=f'{ctx.author.name} is giving away: {prize}!',
                       value=f'React with 🎁 to enter!\n Ends in {round(time / 60, 2)} minutes!', inline=False)
        end = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
        give.set_footer(text=f'Giveaway ends at {end} UTC!')
        my_message = await channel.send(embed=give)

        await my_message.add_reaction("🎁")
        await asyncio.sleep(time)

        new_message = await channel.fetch_message(my_message.id)

        users = await new_message.reactions[0].users().flatten()
        users.pop(users.index(self.bot.user))
        winner = random.choice(users)

        try:
            winning_announcement = discord.Embed(color=discord.Color.red())
            winning_announcement.set_author(name=f'THE GIVEAWAY HAS ENDED!', icon_url='https://i.imgur.com/DDric14.png')
            winning_announcement.add_field(name=f'🎉 Prize: {prize}', value=f'🥳 **Winner**: {winner.mention}\n 🎫 **Number of Entrants**: {len(users)}', inline=False)
            winning_announcement.set_footer(text='Thanks for entering!')
            await channel.send(embed=winning_announcement)
        except IndexError:
            await ctx.send("Nobody join? Maybe next time. Good luck")


def setup(bot):
    bot.add_cog(Giveaway(bot))
