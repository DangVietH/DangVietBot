from discord.ext import commands
import random


class Game(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(help="Play rock paper scissors with the bot")
    async def rps(self, ctx, user_choice):
        rpsGame = ['rock', 'paper', 'scissors']
        comp_choice = random.choice(rpsGame)

        if user_choice == 'rock':
            if comp_choice == 'rock':
                await ctx.send(f'Well, that was weird. We tied.\nYour choice: {user_choice}\nMy choice: {comp_choice}')
            elif comp_choice == "paper":
                await ctx.send('HAHA I WON.!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
            elif comp_choice == 'scissors':
                await ctx.send(
                    f"Bruh. >:\nYour choice: {user_choice}\nMy choice: {comp_choice}")

        elif user_choice == 'paper':
            if comp_choice == 'rock':
                await ctx.send(f'Bruh. >:\nYour choice: {user_choice}\nMy choice: {comp_choice}')
            elif comp_choice == 'paper':
                await ctx.send(f'Well, that was weird. We tied.\nYour choice: {user_choice}\nMy choice: {comp_choice}')
            elif comp_choice == 'scissors':
                await ctx.send(f"HAHA I WON.\nYour choice: {user_choice}\nMy choice: {comp_choice}")

        elif user_choice == 'scissors':
            if comp_choice == 'rock':
                await ctx.send(f'HAHA I WON.\nYour choice: {user_choice}\nMy choice: {comp_choice}')
            elif comp_choice == 'paper':
                await ctx.send(f'Bruh. >: |\nYour choice: {user_choice}\nMy choice: {comp_choice}')
            elif comp_choice == 'scissors':
                await ctx.send(f"Well, that was weird. We tied.\nYour choice: {user_choice}\nMy choice: {comp_choice}")
        else:
            await ctx.send('It must be rock paper scissors')


def setup(client):
    client.add_cog(Game(client))
