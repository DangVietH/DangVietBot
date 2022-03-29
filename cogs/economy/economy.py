import discord
from discord.ext import commands
import random
from motor.motor_asyncio import AsyncIOMotorClient
from utils.menuUtils import DefaultPageSource
from discord.ext.menus.views import ViewMenuPages
from utils.configs import config_var
import asyncio

cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["economy"]
cursor = db["users"]
nfts = db["nft"]

items_name = ["chicken", "parrot", "watch", "horse", "sword", "rifle", "laptop", "platinum", "silver", "gold",
              "diamonds",
              "robber-shield"]
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

        pages = ViewMenuPages(source=DefaultPageSource(f"Richest user in {ctx.guild.name}", data), clear_reactions_after=True)
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

        pages = ViewMenuPages(source=DefaultPageSource(f"Richest user in the world", data), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(help="Beg some money")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def beg(self, ctx):
        user = ctx.author

        await self.open_account(user)

        random_money = random.randint(1, 1000)
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": random_money}})
        await ctx.send(f"Someone gave you 💵 {random_money}")

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        await self.open_account(ctx.author)

        name = ['tim', 'bill', 'jack', 'jim']
        verb = ['ate', 'kicked', 'drank', 'paid']
        noun = ['a cat', 'a shopkeeper', 'a ball', 'a horse']

        sentences = f"{name[random.randint(0, 3)]} {verb[random.randint(0, 3)]} {noun[random.randint(0, 3)]}"
        emojis = []
        for s in sentences:
            if s.isdecimal():
                num2emo = {'0': 'zero', '1': 'one', '2': 'two',
                           '3': 'three', '4': 'four', '5': 'five',
                           '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
                emojis.append(f":{num2emo.get(s)}:")
            elif s.isalpha():
                emojis.append(f":regional_indicator_{s.lower()}:")
            else:
                emojis.append(s)
        await ctx.send('Convert these emojis to text')
        await ctx.send(''.join(emojis))

        def check(user):
            return user.author == ctx.author and user.channel == ctx.channel

        embed = discord.Embed(timestamp=ctx.message.created_at)
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            lowMone = random.randint(1, 100)
            embed.title = "BAD WORK"
            embed.description = f"You took too long to respond. You're paid 💵 {lowMone}"
            embed.color = discord.Color.red()
            await ctx.send(embed=embed)
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": lowMone}})
        else:
            if msg.content.lower() == sentences.lower():
                ymone = random.randint(1000, 100000)
                embed.title = "GOOD WORK"
                embed.description = f"You got paid 💵 {ymone} for successfully converting the emojis to text"
                embed.color = discord.Color.green()
                await ctx.send(embed=embed)
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": ymone}})
            else:
                lowMone = random.randint(1, 100)
                embed.title = "FAIL"
                embed.description = f"You're paid 💵 {lowMone} for unsuccessfully converting the emojis to text"
                embed.color = discord.Color.red()
                await ctx.send(embed=embed)
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": lowMone}})

    @commands.command(help="View the store", aliases=['store'])
    async def shop(self, ctx):
        data = []
        for i in range(len(items_name)):
            data.append((f"{items_name[i]} | 💵 {items_price[i]}",
                         items_description[i]))
        page = ViewMenuPages(source=DefaultPageSource(f"Shop", data), clear_reactions_after=True)
        await page.start(ctx)

    @commands.command(help="Buy some items")
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
                        return await ctx.send("You don't have enough money in your wallet")
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
    async def sell(self, ctx, item_name: str, amount=1):
        user = ctx.author

        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        item_name = item_name.lower()
        name = None
        price = None
        amounts = None

        for item in check['inventory']:
            if item['name'].lower() == item_name:
                name = item['name']
                amounts = item['amount']
                price = item["price"]
                break

        if name is None:
            return await ctx.send("Item not in inventory")
        if amounts < amount:
            return await ctx.send(f"You do not have enough {item_name} in the inventory")
        await cursor.update_one({"id": user.id, "inventory.name": str(item_name)},
                                {"$inc": {"inventory.$.amount": -amount}})

        is_amount_zero = await cursor.find_one(
            {"id": user.id, "inventory.name": str(item_name), "inventory.amount": 0})
        if is_amount_zero is not None:
            await cursor.update_one({"id": user.id}, {"$pull": {"inventory": {"name": item_name}}})
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": amounts * price}})
        await ctx.send(f"Successfully sold {amount} {item_name} for 💵 {price}")

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
            pages = ViewMenuPages(source=DefaultPageSource(f"{ctx.author} Inventory", data), clear_reactions_after=True)
            await pages.start(ctx)

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
    async def gamble(self, ctx, amount: int):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})
        if check['wallet'] < amount:
            return await ctx.send("Too much")
        elif amount <= 0:
            return await ctx.send("Too less")
        chance = random.randint(1, 100)
        if chance <= 50:
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": amount}})
            await ctx.send(f"You just won 💵 {amount}")
        else:
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
            await ctx.send(f"You have lost 💵 {amount}")

    @commands.command(help="Deposit your money into the bank", aliases=['dep'])
    async def deposit(self, ctx, amount=None):
        user = ctx.author
        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        if amount.lower() == "all":
            await cursor.update_one({"id": user.id}, {"$inc": {"bank": check['wallet']}})
            await cursor.update_one({"id": user.id}, {"$set": {"wallet": 0}})
            await ctx.message.add_reaction("✅")
            return
        amount = int(amount)
        if amount > check['wallet']:
            return await ctx.send("You can't deposit more money than your wallet")
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": -amount}})
        await cursor.update_one({"id": user.id}, {"$inc": {"bank": amount}})
        await ctx.message.add_reaction("✅")

    @commands.command(help="Withdraw your money from the bank")
    async def withdraw(self, ctx, amount=None):
        user = ctx.author
        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        if amount.lower() == "all":
            await cursor.update_one({"id": user.id}, {"$inc": {"wallet": check['bank']}})
            await cursor.update_one({"id": user.id}, {"$set": {"bank": 0}})
            await ctx.message.add_reaction("✅")
            return
        amount = int(amount)
        if amount > check['bank']:
            return await ctx.send("You can't deposit more money than your bank")
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": amount}})
        await cursor.update_one({"id": user.id}, {"$inc": {"bank": -amount}})
        await ctx.message.add_reaction("✅")

    @commands.command(help="Transfer money to someone", aliases=['send'])
    async def transfer(self, ctx, user: discord.Member = None, amount=1):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            return await ctx.send("They don't have an economy account")
        if amount > check['wallet']:
            return await ctx.send("You didn't have enough money in your bank to give someone")
        await cursor.update_one({"id": ctx.author.id}, {"$inc": {"bank": -amount}})
        await cursor.update_one({"id": user.id}, {"$inc": {"bank": amount}})
        await ctx.message.add_reaction("✅")
        await user.send(f"**{ctx.author}** just gave you 💵 {amount}")

    @commands.command(help="It's a crime to steal someone", aliases=['steal'])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def rob(self, ctx, user: discord.Member = None, amount=1):
        await self.open_account(ctx.author)

        check1 = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            return await ctx.send("They haven't registered yet")
        total_check = check1['wallet'] + check1['bank']
        if total_check < 10000:
            return await ctx.send("You need 💵 10000 to rob someone")
        anti_rob_1 = await cursor.find_one({"id": user.id, "inventory.name": "robber-shield"})
        if anti_rob_1 is not None:
            author_update = check1['wallet'] + 10
            user_update = check2['wallet'] - 10
            await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
            await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})
            await ctx.send(f"You tried to rob him but you only got 💵 10")
            return
        if amount > check2['wallet']:
            await ctx.send(
                'You tried to rob him, but he caught you and force you to pay 💵 1000')
            author_update = check1['wallet'] - 1000
            user_update = check2['wallet'] + 1000
            await cursor.update_one({"id": ctx.author.id}, {"$set": {"wallet": author_update}})
            await cursor.update_one({"id": user.id}, {"$set": {"wallet": user_update}})
            return
        else:
            author_update = check1['wallet'] + amount
            user_update = check2['wallet'] - amount
            await cursor.update_one({"id": ctx.author.id}, {"$set": {"wallet": author_update}})
            await cursor.update_one({"id": user.id}, {"$set": {"wallet": user_update}})
            await ctx.send(f"Successfully rob 💵 {amount} from {user.mention}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if self.bot.get_user(member.id) is None:
            if await cursor.find_one({"id": member.id}):
                await cursor.delete_one({"id": member.id})