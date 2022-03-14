import discord
from discord.ext import commands
import random
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from cogs.economy.econUtils import InventoryPageSource, GuildRichPageSource, GlobalRichPageSource, ShopPageSource, NFTPageSource
from discord.ext.menus.views import ViewMenuPages
from utils.configs import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["economy"]
cursor = db["users"]
nfts = db["nft"]

items_name = ["chicken", "parrot", "watch", "horse", "sword", "rifle", "laptop", "platinum", "silver", "gold",
              "diamonds",
              "robber_shield"]
items_price = [10, 20, 42, 70, 102, 499, 1000, 20000, 50000, 200000, 599999, 1542649]
items_description = ["KFC GO BRRR", "talking birb machine", "moniter ye time", "Juan",
                     "fight others", "hunt animals", "work on it", "Show of your status", "cool kid",
                     "rich kid who like to show off", "extremely rich kid", "They can only nick a little"]


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def open_account(self, user):
        users = await cursor.find_one({"id": user.id})
        if users is None:
            insert = {"id": user.id, "job": "None", "wallet": 0, "bank": 0, "inventory": [], "rank": "None", "stock": "None"}
            await cursor.insert_one(insert)
        else:
            return None

    @commands.command(help="See how much money you have", aliases=["bal"])
    async def balance(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        if not user.bot:
            await self.open_account(user)

            check = await cursor.find_one({"id": user.id})
            wallet = check['wallet']
            bank = check['bank']
            balance = wallet + bank
            embed = discord.Embed(description=f"**Total:** 💵 {balance}",
                                  color=discord.Color.blue())
            embed.set_author(
                icon_url=user.avatar.url,
                name=f"{user} balance")
            embed.add_field(name="Wallet", value=f"💵 {wallet}", inline=False)
            embed.add_field(name="Bank", value=f"💵 {bank}", inline=False)
            await ctx.send(embed=embed)

    @commands.command(help="Who is the richest one in your server")
    @commands.guild_only()
    async def rich(self, ctx):
        stats = cursor.find().sort("wallet", -1)
        data = []
        num = 0
        async for x in stats:
            is_user_in_guild = ctx.guild.get_member(x['id'])
            if is_user_in_guild is not None:
                num += 1
                to_append = (f"{num}: {is_user_in_guild}", f"**Wallet:** {x['wallet']}")
                data.append(to_append)

        pages = ViewMenuPages(source=GuildRichPageSource(data), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(help="Who is the richest one around the world")
    async def grich(self, ctx):
        stats = cursor.find().sort("wallet", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {self.bot.get_user(x['id'])}", f"**Wallet:** {x['wallet']}")
            data.append(to_append)

        pages = ViewMenuPages(source=GlobalRichPageSource(data), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(help="Beg some money")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    @commands.guild_only()
    async def beg(self, ctx):
        user = ctx.author

        await self.open_account(user)

        random_money = random.randint(1, 1000)
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": random_money}})
        await ctx.send(f"Someone gave you 💵 {random_money}")

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @commands.guild_only()
    async def work(self, ctx):
        user = ctx.author
        await self.open_account(user)

        check = await cursor.find_one({"id": user.id})
        random_money = random.randint(100, 10000)
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": random_money}})
        jl = ['police', 'programmer', 'bus driver', 'street preformer', 'taxi driver', 'farmer', 'teacher', 'doctor']
        career = random.choice(jl)
        await ctx.send(f"You got 💵 {random_money} for working as a {career}")

    @commands.command(help="View the store", aliases=['store'])
    @commands.guild_only()
    async def shop(self, ctx):
        data = []
        for i in range(len(items_name)):
            data.append((f"{items_name[i]} | 💵 {items_price[i]}",
                         items_description[i]))
        page = MenuButtons(source=ShopPageSource(data), disable_buttons_after=True, ctx=ctx)
        await page.start(ctx)

    @commands.command(help="Buy some items")
    @commands.guild_only()
    async def buy(self, ctx, item_name: str, amount=1):
        user = ctx.author

        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})
        item_name = item_name.lower()
        if item_name not in items_name:
            await ctx.send("Item does not exist in shop")
        else:
            for i in range(len(items_name)):
                if item_name == str(items_name[i]):
                    cost = int(items_price[i]) * amount
                    if cost > check['wallet']:
                        await ctx.send("You don't have enough money in your wallet")
                    else:
                        inventory_check = await cursor.find_one({"id": user.id, "inventory.name": str(item_name)})
                        if inventory_check is None:
                            await cursor.update_one({"id": user.id},
                                                    {"$push": {"inventory": {"name": item_name,
                                                                             "price": int(items_price[i]),
                                                                             "amount": int(amount)}}})
                        else:
                            await cursor.update_one({"id": user.id, "inventory.name": str(item_name)},
                                                    {"$inc": {"inventory.$.amount": int(amount)}})
                        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": -cost}})
                        await ctx.send(
                            f"You just brought {amount} {item_name} that cost 💵 {cost}")
                    break

    @commands.command(help="Sell your items")
    @commands.guild_only()
    async def sell(self, ctx, item_name: str, amount=1):
        user = ctx.author

        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        item_name = item_name.lower()
        for item in check['inventory']:
            if item['name'].lower() == item_name:
                amounts = item['amount']
                price = item["price"]
                if amounts < amount:
                    await ctx.send("Too much")
                else:
                    await cursor.update_one({"id": user.id, "inventory.name": str(item_name)},
                                            {"$inc": {"inventory.$.amount": -amount}})

                    is_amount_zero = await cursor.find_one(
                        {"id": user.id, "inventory.name": str(item_name), "inventory.amount": 0})
                    if is_amount_zero is not None:
                        await cursor.update_one({"id": user.id}, {"$pull": {"inventory": {"name": item_name}}})
                    await cursor.update_one({"id": user.id}, {"$inc": {"wallet": amounts * price}})
                    await ctx.send(f"Successfully sold {amount} {item_name} for 💵 {price}")
                break

    @commands.command(help="See your items", aliases=["bag"])
    async def inventory(self, ctx):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})

        data = []
        items = check['inventory']
        if len(items) < 1:
            await ctx.send("You didn't have anything")
        else:
            for item in items:
                name = item['name']
                amount = item['amount']
                to_append = (f"{name}", f"**Amount** {amount}")
                data.append(to_append)
            page = ViewMenuPages(source=InventoryPageSource(data), clear_reactions_after=True)
            await page.start(ctx)

    @commands.command(help="Claim your daily money")
    @commands.cooldown(1, 60 * 60 * 24, commands.BucketType.user)
    async def daily(self, ctx):
        await self.open_account(ctx.author)
        await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": 90000}})
        await ctx.send(
            embed=discord.Embed(title="Daily Claimed", description="You just got 90000 💵",
                                color=discord.Color.green()))

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    async def gamble(self, ctx, amount: int):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})
        if check['wallet'] < amount:
            await ctx.send("Too much")
        elif amount <= 0:
            await ctx.send("Too less")
        else:
            chance = random.randint(1, 100)
            if chance <= 50:
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": amount}})
                await ctx.send(f"You just won 💵 {amount}")
            else:
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                await ctx.send(f"You have lost 💵 {amount}")

    @commands.command(help="Deposit your money into the bank", aliases=['dep'])
    @commands.guild_only()
    async def deposit(self, ctx, amount=None):
        user = ctx.author
        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        if amount.lower() == "all":
            await cursor.update_one({"id": user.id}, {"$inc": {"bank": check['wallet']}})
            await cursor.update_one({"id": user.id}, {"$set": {"wallet": 0}})
            await ctx.message.add_reaction("✅")
        else:
            amount = int(amount)
            if amount > check['wallet']:
                await ctx.send("You can't deposit more money than your wallet")
            else:
                await cursor.update_one({"id": user.id}, {"$inc": {"wallet": -amount}})
                await cursor.update_one({"id": user.id}, {"$inc": {"bank": amount}})
                await ctx.message.add_reaction("✅")

    @commands.command(help="Withdraw your money from the bank")
    @commands.guild_only()
    async def withdraw(self, ctx, amount=None):
        user = ctx.author
        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        if amount.lower() == "all":
            await cursor.update_one({"id": user.id}, {"$inc": {"wallet": check['bank']}})
            await cursor.update_one({"id": user.id}, {"$set": {"bank": 0}})
            await ctx.message.add_reaction("✅")

        else:
            amount = int(amount)
            if amount > check['bank']:
                await ctx.send("You can't deposit more money than your bank")
            else:
                await cursor.update_one({"id": user.id}, {"$inc": {"wallet": amount}})
                await cursor.update_one({"id": user.id}, {"$inc": {"bank": -amount}})
                await ctx.message.add_reaction("✅")

    @commands.command(help="Transfer money to someone", aliases=['send'])
    @commands.guild_only()
    async def transfer(self, ctx, user: discord.Member = None, amount=1):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            await ctx.send("They don't have an economy account")
        else:
            if amount > check['wallet']:
                await ctx.send("You didn't have enough money in your bank to give someone")
            else:
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"bank": -amount}})
                await cursor.update_one({"id": user.id}, {"$inc": {"bank": amount}})
                await ctx.message.add_reaction("✅")
                await user.send(f"**{ctx.author}** just gave you 💵 {amount}")

    @commands.command(help="It's a crime to steal someone", aliases=['steal'])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    @commands.guild_only()
    async def rob(self, ctx, user: discord.Member = None, amount=1):
        await self.open_account(ctx.author)

        check1 = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            await ctx.send("They haven't registered yet")
        else:
            total_check = check1['wallet'] + check1['bank']
            if total_check < 10000:
                await ctx.send("You need 💵 10000 to rob someone")
            else:
                anti_rob_1 = await cursor.find_one({"id": user.id, "inventory.name": "robber_shield"})
                if anti_rob_1 is not None:
                    author_update = check1['wallet'] + 10
                    user_update = check2['wallet'] - 10
                    await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
                    await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})
                    await ctx.send(f"You tried to rob him but you only got 💵 10")

                if amount > check2['wallet']:
                    await ctx.send(
                        'You tried to rob him, but he caught you and force you to pay 💵 1000')
                    author_update = check1['wallet'] - 1000
                    user_update = check2['wallet'] + 1000
                    await cursor.update_one({"id": ctx.author.id}, {"$set": {"wallet": author_update}})
                    await cursor.update_one({"id": user.id}, {"$set": {"wallet": user_update}})

                else:
                    author_update = check1['wallet'] + amount
                    user_update = check2['wallet'] - amount
                    await cursor.update_one({"id": ctx.author.id}, {"$set": {"wallet": author_update}})
                    await cursor.update_one({"id": user.id}, {"$set": {"wallet": user_update}})
                    await ctx.send(f"Successfully rob 💵 {amount} from {user.mention}")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="IT'S SCREENSHOT TIME!")
    async def nft(self, ctx):
        embed = discord.Embed(title="Nft", color=discord.Color.random())
        command = self.bot.get_command("nft")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"nft {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @nft.command(help="Create an nft")
    async def create(self, ctx):
        await self.open_account(ctx.author)

        await ctx.send("Answer These Question In 1 minute!")
        questions = ["Enter Name: ", "Enter Image link: "]
        answers = []

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        for question in questions:
            await ctx.send(question)

            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Type Faster Next Time!")
                return
            else:
                answers.append(msg.content)

        check = await nfts.find_one({"name": answers[0]})
        if check is not None:
            await ctx.send("NFT already exists")
        else:
            price = random.randint(1, 100000)
            await nfts.insert_one({"name": answers[0], "link": answers[1], "price": price, "owner": ctx.author.id})
            await ctx.send(f"NFT {answers[0]} created for 💵 {price}")

    @nft.command(help="WHY DON'T SCREENSHOT", aliases=["buy"])
    async def purchase(self, ctx, *, name):
        await self.open_account(ctx.author)
        check = await nfts.find_one({"name": name})
        if check is None:
            await ctx.send("NFT do not exist. Also nft are CASE SENSITIVE")
        else:
            user = await cursor.find_one({"id": ctx.author.id})
            if user['wallet'] < check['price']:
                await ctx.send("You don't have enough FireCoin")
            else:
                og_owner = self.bot.get_user(check['owner'])
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -check['price']}})
                await cursor.update_one({"id": og_owner.id}, {"$inc": {"wallet": check['price']}})
                await cursor.update_one({"id": og_owner.id}, {"$inc": {"price": random.randint(1, 1000)}})
                await nfts.update_one({"name": name}, {"$set": {"owner": ctx.author.id}})
                await ctx.send("Successfully bought the nft. **REMEMBER THAT NFTS IS DESTROYING OUR PLANET!**")
                await og_owner.send(
                    f"**{ctx.author}** just bought your nft name **{name}** and you receive 💵 {check['price']}")

    @nft.command(help="IT'S SCREENSHOT TIME")
    async def view(self, ctx, *, name):
        check = await nfts.find_one({"name": name})
        if check is None:
            await ctx.send("NFT do not exist. Also nft are CASE SENSITIVE")
        else:
            embed = discord.Embed(title=f"{check['name']}",
                                  description=f"**Price:** 💵 {check['price']} \n**Owner:** {self.bot.get_user(check['owner'])}",
                                  color=discord.Color.from_rgb(225, 0, 92))
            embed.set_image(url=check['link'])
            await ctx.send(embed=embed)

    @nft.command(help="after someone just screenshot it")
    @commands.is_owner()
    async def delete(self, ctx, *, name):
        check = await nfts.find_one({"name": name})
        if check is None:
            await ctx.send("NFT do not exist. Also nft are CASE SENSITIVE")
        else:
            og_owner = self.bot.get_user(check['owner'])
            await nfts.delete_one({"name": name})
            await ctx.send("NFT deleted")
            await og_owner.send(f"Your nft just get deleted by the bot developer!")

    @nft.command(help="View all nfts to screenshot")
    async def list(self, ctx):
        stats = nfts.find()
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}. {x['name']}",
                         f"**Price:** 💵 {x['price']} **Owner:** {self.bot.get_user(x['owner'])}")
            data.append(to_append)
        page = ViewMenuPages(source=NFTPageSource(data), clear_reactions_after=True)
        await page.start(ctx)
