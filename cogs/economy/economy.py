import discord
from discord.ext import commands
import random
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from cogs.economy.shopping_list import shop

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["economy"]
cursor = db["users"]

NO_ACCOUNT = "You don't have an economy account. Please use the create_account command to create one"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Create your economy account")
    async def create_account(self, ctx):
        check = await cursor.find_one({"id": ctx.author.id})
        if check is None:
            insert = {"id": ctx.author.id, "wallet": 0, "bank": 0, "inventory": []}
            await cursor.insert_one(insert)
            await ctx.send(
                "Done, your economy account has been created. **ONLY USE OUR CURRENCY IN THE BOT. IF YOU'RE CAUGHT USING THIS BOT TO TRADE REAL LIFE ITEMS, YOU'RE DEAD!!**")
        else:
            await ctx.send("You already have an account")

    @commands.command(help="See how much money you have", aliases=["bal"])
    async def balance(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        check = await cursor.find_one({"id": user.id})
        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            wallet = check['wallet']
            bank = check['bank']
            balance = wallet + bank
            embed = discord.Embed(title=f"{user} balance",
                                  description=f"**Total:** <:DHBuck:901485795410599988> {balance}",
                                  color=discord.Color.blue())
            embed.add_field(name="Wallet", value=f"<:DHBuck:901485795410599988> {wallet}", inline=False)
            embed.add_field(name="Bank", value=f"<:DHBuck:901485795410599988> {bank}", inline=False)
            await ctx.send(embed=embed)

    @commands.command(help="Beg some money")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def beg(self, ctx):
        user = ctx.author
        check = await cursor.find_one({"id": user.id})
        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            random_money = random.randint(1, 1000)
            newBal = check['wallet'] + random_money
            await cursor.update_one({"id": user.id}, {"$set": {"wallet": newBal}})
            await ctx.send(f"Someone gave you <:DHBuck:901485795410599988> {random_money}")

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        user = ctx.author

        name = ["Tom", "John", "Jim", "Jack", "Henry", "Tim", "Lucas"]
        verbs = ["eat", "drink", "kicked", "paid", "build", "throw", "buy"]
        noun = ['a cat', 'the cashier', 'a ball', "an apple", 'a house', 'a bee', 'a cow', 'a computer']

        check = await cursor.find_one({"id": user.id})
        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            emojis = []
            sentence = f"{name[random.randint(0, len(name) - 1)]} {verbs[random.randint(0, len(verbs) - 1)]} {noun[random.randint(0, len(noun) - 1)]}"

            for s in sentence:
                if s.isalpha():
                    emojis.append(f":regional_indicator_{s.lower()}:")
                else:
                    emojis.append("  ")
            await ctx.send("Convert the message below to text")
            await ctx.send(' '.join(emojis))
            try:
                message = await self.bot.wait_for('message', timeout=30.0)
            except asyncio.TimeoutError:
                newBal = check['wallet'] + 10
                await cursor.update_one({"id": user.id}, {"$set": {"wallet": newBal}})
                embed = discord.Embed(title="🤦 BAD WORK 🤦",
                                      description="You didn't complete in time? You only receive <:DHBuck:901485795410599988> 10 because of that!!",
                                      color=discord.Color.red())
                await ctx.send(embed=embed)
            else:
                if message.content.lower() == sentence.lower():
                    random_money = random.randint(100, 10000)
                    newBal = check['wallet'] + random_money
                    await cursor.update_one({"id": user.id}, {"$set": {"wallet": newBal}})
                    embed = discord.Embed(title="GOOD JOB",
                                          description=f"Your receive <:DHBuck:901485795410599988> {random_money} for successfully converting it to a text",
                                          color=discord.Color.green())
                    await message.reply(embed=embed)
                else:
                    low_money = random.randint(10, 100)
                    newBal = check['wallet'] + low_money
                    await cursor.update_one({"id": user.id}, {"$set": {"wallet": newBal}})
                    embed = discord.Embed(title="🤦 BAD WORK 🤦",
                                          description=f"You didn't answer correctly. You only receive <:DHBuck:901485795410599988> {low_money}",
                                          color=discord.Color.red())
                    await message.reply(embed=embed)

    @commands.command(help="Shopping list", aliases=["shoplist", 'sl'])
    async def shop(self, ctx):
        embed = discord.Embed(title="🏪 Shop", color=discord.Color.green())

        for item in shop:
            name = item["name"]
            price = item["price"]
            description = item["description"]
            embed.add_field(name=name, value=f"<:DHBuck:901485795410599988>  {price} | Description: {description}",
                            inline=False)

        await ctx.send(embed=embed)

    @commands.command(help="Buy stuff")
    async def buy(self, ctx, item_name, amount=1):
        user = ctx.author
        check = await cursor.find_one({"id": user.id})

        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            item_name = item_name.lower()
            name_ = None
            price = None

            for item in shop:
                name = item["name"].lower()
                if name == item_name:
                    name_ = name
                    price = item["price"]
                    break

            if name_ is None:
                await ctx.send("That item didn't exist")
            wallet = check['wallet']
            cost = price * amount
            if cost > wallet:
                await ctx.send(f"You don't have enough money to buy {amount} {item_name}")
            else:
                inventory_check = await cursor.find_one({"id": user.id, "inventory.name": str(item_name)})
                if inventory_check is None:
                    await cursor.update_one({"id": user.id},
                                            {"$push": {"inventory": {"name": item_name, "amount": int(amount)}}})
                else:
                    await cursor.update_one({"id": user.id, "inventory.name": str(item_name)},
                                            {"$inc": {"inventory.$.amount": int(amount)}})
                # get ye money
                newBal = wallet - cost
                await cursor.update_one({"id": user.id}, {"$set": {"wallet": newBal}})
                await ctx.send(f"You just brought {amount} {item_name} that cost <:DHBuck:901485795410599988>  {cost}")

    @commands.command(help="Sell your items")
    async def sell(self, ctx, item_name, amount=1):
        user = ctx.author
        check = await cursor.find_one({"id": user.id})

        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            item_name = item_name.lower()
            name_ = None
            price = None

            for item in shop:
                name = item["name"].lower()
                if name == item_name:
                    name_ = name
                    price = item["price"]
                    break

            if name_ is None:
                await ctx.send("That item didn't exist")

            inventory_check = await cursor.find_one({"id": user.id, "inventory.name": str(item_name)})
            if inventory_check is None:
                await ctx.send("Not in your inventory")
            else:
                if await cursor.find_one({"id": user.id, "inventory.name": str(item_name)}) < amount:
                    await ctx.send("Too much")
                else:
                    if await cursor.find_one({"id": user.id, "inventory.name": str(item_name)},
                                             {"$elemMatch ": {"inventory.$.amount"}}) < amount:
                        await ctx.send(f"You don't have enough {item_name} in your inventory")
                    else:
                        if await cursor.find_one({"id": user.id, "inventory.name": str(item_name)},
                                                 {"$elemMatch ": {"inventory.$.amount"}}) == amount:
                            await cursor.update_one({"id": user.id}, {"$pull": {"inventory": {"name": str(item_name)}}})
                        else:
                            await cursor.update_one({"id": user.id, "inventory.name": str(item_name)},
                                                    {"$inc": {"inventory.$.amount": -amount}})
                        newBal = check['wallet'] + amount * price
                        await cursor.update_one({"id": user.id}, {"$set": {"wallet": newBal}})
                        await ctx.send(
                            f"You just sold {amount} {item_name} and get <:DHBuck:901485795410599988> {amount * price}")

    @commands.command(help="See your items", aliases=["bag"])
    async def inventory(self, ctx):
        check = await cursor.find_one({"id": ctx.author.id})
        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            embed = discord.Embed(title=f"🧳 {ctx.author}'s Inventory", color=discord.Color.random())
            items = check['inventory']
            if len(items) < 1:
                await ctx.send("You didn't have anything")
            else:
                for item in items:
                    name = item['name']
                    amount = item['amount']
                    embed.add_field(name=name, value=f"**Amount:** {amount}")
                await ctx.send(embed=embed)

    @commands.command(help="Deposit your money into the bank", aliases=['dep'])
    async def deposit(self, ctx, amount=1):
        user = ctx.author
        check = await cursor.find_one({"id": user.id})

        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            wallet = check['wallet']
            bank = check['bank']
            if amount > wallet:
                await ctx.send("You can't deposit more money than your wallet")
            else:
                newWallet = wallet - amount
                newBank = bank + amount
                await cursor.update_one({"id": user.id}, {"$set": {"wallet": newWallet}})
                await cursor.update_one({"id": user.id}, {"$set": {"bank": newBank}})
                await ctx.message.add_reaction("✅")

    @commands.command(help="Withdraw your money from the bank")
    async def withdraw(self, ctx, amount=1):
        user = ctx.author
        check = await cursor.find_one({"id": user.id})

        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            wallet = check['wallet']
            bank = check['bank']
            if amount > bank:
                await ctx.send("You can't deposit more money than your bank")
            else:
                newWallet = wallet + amount
                newBank = bank - amount
                await cursor.update_one({"id": user.id}, {"$set": {"wallet": newWallet}})
                await cursor.update_one({"id": user.id}, {"$set": {"bank": newBank}})
                await ctx.message.add_reaction("✅")

    @commands.command(help="Transfer money to someone", aliases=['send'])
    async def transfer(self, ctx, user: discord.Member = None, amount=1):
        check1 = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            await ctx.send("They don't have an economy account")
        elif check1 is None:
            await ctx.send(NO_ACCOUNT)
        else:
            if amount > check1['wallet']:
                await ctx.send("You didn't have enough money in your bank to give someone")
            else:
                author_update = check1['bank'] - amount
                user_update = check2['bank'] + amount
                await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
                await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})
                await ctx.message.add_reaction("✅")
                await user.send(f"**{ctx.author}** just gave you <:DHBuck:901485795410599988> {amount}")

    @commands.command(help="It's a crime to steal someone", aliases=['steal'])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def rob(self, ctx, user: discord.Member = None, amount=1):
        check1 = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            await ctx.send("They don't have an economy account")
        elif check1 is None:
            await ctx.send(NO_ACCOUNT)
        else:
            total_check = check1['wallet'] + check1['bank']
            if total_check < 10000:
                await ctx.send("You need <:DHBuck:901485795410599988> 10000 to rob someone")
            else:
                victim_items = check2['inventory']
                for item in victim_items:
                    if item['name'] == "robber_shield":
                        author_update = check1['wallet'] + 10
                        user_update = check2['wallet'] - 10
                        await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
                        await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})
                        await ctx.send(
                            "Your victim has a robber shield, so you can only rob <:DHBuck:901485795410599988> 10 from him")

                if amount > check2['wallet']:
                    await ctx.send(
                        'You tried to rob him, but he caught you and force you to pay <:DHB_coin:901485795410599988> 1000')
                    author_update = check1['wallet'] - 1000
                    user_update = check2['bank'] + 1000
                    await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
                    await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})

                else:
                    author_update = check1['wallet'] + amount
                    user_update = check2['wallet'] - amount
                    await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
                    await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})
                    await ctx.send(f"Successfully rob <:DHBuck:901485795410599988> {amount} from {user.mention}")
