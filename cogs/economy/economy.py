import discord
from discord.ext import commands
import random
from utils import DefaultPageSource, MenuPages
import asyncio


class Economy(commands.Cog):
    emoji = "💰"

    def __init__(self, bot):
        self.bot = bot
        self.serverdata = self.bot.mongo["economy"]["server"]
        self.economy = self.bot.mongo["economy"]["member"]

    async def open_account(self, user):
        users = await self.economy.find_one({"guild": user.guild.id, "user": user.id})
        if users is None:
            if await self.economy.find_one({"id": user.id}):
                return
            await self.economy.insert_one({"guild": user.guild.id, "user": user.id, "wallet": 0, "bank": 0, "inventory": []})

    @commands.command(help="See how much money you have", aliases=["bal"])
    async def balance(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        if not user.bot:

            stats = await self.economy.find_one({"guild": user.guild.id, "user": user.id})
            balance = stats['wallet'] + stats['bank']
            embed = discord.Embed(description=f"**Total:** {(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {balance}",
                                  color=discord.Color.blue())
            embed.set_author(
                icon_url=user.avatar.url,
                name=f"{user} balance")
            embed.add_field(name="Wallet", value=f"{(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {stats['wallet']}", inline=False)
            embed.add_field(name="Bank", value=f"{(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {stats['bank']}", inline=False)
            await ctx.send(embed=embed)

    @commands.command(help="Claim your daily money")
    @commands.cooldown(1, 60 * 60 * 24, commands.BucketType.user)
    async def daily(self, ctx):
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": (await self.serverdata.find_one({"guild": ctx.guild.id}))['daily']}})
        await ctx.send("You claimed your daily money! You now have {} {}.".format((await self.serverdata.find_one({"guild": ctx.guild.id}))['econ_symbol'], (await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id}))['wallet']))

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Check the shop")
    async def shop(self, ctx):
        data = await self.serverdata.find_one({"guild": ctx.guild.id})
        items = data['shop']
        if len(items) < 1:
            return await ctx.send("There's nothing in the shop! If you have the manage_guild permission, use `{}shop add` to add items.".format(ctx.prefix))
        data = []
        for item in items:
            name = item['name']
            amount = item['amount']
            data.append((f"{name}", f"**Price** {amount}"))
        pages = MenuPages(DefaultPageSource(f"{ctx.guild} Shop!", data), ctx)
        await pages.start()

    @shop.command(name="add", help="Add item to the shop")
    @commands.has_permissions(manage_guild=True)
    async def shop_add(self, ctx, name: str, price: int):
        await self.serverdata.update_one({"guild": ctx.guild.id}, {"$addToSet": {"shop": {"name": name, "price": price}}})
        await ctx.send(f"Added {name} to the shop!")

    @shop.command(name="remove", help="Remove an item from the shop")
    @commands.has_permissions(manage_guild=True)
    async def shop_remove(self, ctx, name: str):
        data = await self.serverdata.find_one({"guild": ctx.guild.id, "shop.name": name})
        if data is None:
            return await ctx.send("That item isn't in the shop!")
        await self.serverdata.update_one({"guild": ctx.guild.id}, {"$pull": {"shop": {"name": name}}})
        await ctx.send(f"Removed {name} from the shop!")

    @commands.command(help="Buy some items")
    async def buy(self, ctx, item_name: str, amount=1):
        item_name = item_name.lower()
        check = await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id})

        name = None
        price = None
        for shop_item in (await self.serverdata.find_one({'guild': ctx.guild.id}))['shop']:
            if shop_item['name'].lower() == item_name:
                name = shop_item['name']
                price = shop_item["price"]
                break

        if name is None:
            return await ctx.send("That item isn't in the shop!")
        cost = price * amount
        if cost > check['wallet']:
            return await ctx.send("You don't have enough money in your wallet to buy this item!")
        inventory_check = await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id, "inventory.name": str(item_name)})
        if inventory_check is None:
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id},
                                          {"$addToSet": {"inventory": {"name": item_name,
                                                                       "price": int(price),
                                                                       "amount": amount}}})

        else:
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id, "inventory.name": str(item_name)},
                                          {"$inc": {"inventory.$.amount": int(amount)}})
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id},
                                      {"$inc": {"wallet": -cost}})
        await ctx.send(f"You just brought {amount} {item_name} that cost {(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {cost}")

    @commands.command(help="Sell your items")
    async def sell(self, ctx, item_name: str, amount=1):
        item_name = item_name.lower()
        check = await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id})

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

        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id, "inventory.name": str(item_name)},
                                      {"$inc": {"inventory.$.amount": -amount}})

        is_amount_zero = await self.economy.find_one(
            {"guild": ctx.guild.id, "user": ctx.author.id, "inventory.name": str(item_name), "inventory.amount": 0})
        if is_amount_zero is not None:
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$pull": {"inventory": {"name": item_name}}})
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": amounts * price}})
        await ctx.send(f"Successfully sold {amount} {item_name} for 💵 {price}")

    @commands.command(help="See your items")
    async def inventory(self, ctx):
        check = await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id})

        data = []
        items = check['inventory']
        if len(items) < 1:
            return await ctx.send("You didn't have anything")
        for item in items:
            name = item['name']
            amount = item['amount']
            to_append = (f"{name}", f"**Amount** {amount}")
            data.append(to_append)
        pages = MenuPages(DefaultPageSource(f"{ctx.author} Inventory", data), ctx)
        await pages.start()

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 60 * 60, commands.BucketType.user)
    async def work(self, ctx):

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
        embed.set_footer(text=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            lowMone = random.randint(1, 100)
            embed.title = "BAD WORK"
            embed.description = f"You took too long to respond. You're paid {(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {lowMone}"
            embed.color = discord.Color.red()
            await ctx.send(embed=embed)
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": lowMone}})
        else:
            if msg.content.lower() == sentences.lower():
                ymone = random.randint(1000, 100000)
                embed.title = "GOOD JOB"
                embed.description = f"You got paid {(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {ymone} for successfully converting the emojis to text"
                embed.color = discord.Color.green()
                await ctx.send(embed=embed)
                await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": ymone}})
            else:
                lowMone = random.randint(1, 100)
                embed.title = "FAIL"
                embed.description = f"You're paid {(await self.serverdata.find_one({'guild': ctx.guild.id}))['econ_symbol']} {lowMone} for unsuccessfully converting the emojis to text"
                embed.color = discord.Color.red()
                await ctx.send(embed=embed)
                await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": lowMone}})

    @commands.command(help="Who is the richest one in your server")
    async def rich(self, ctx):
        stats = self.economy.find({"guild": ctx.guild.id}).sort("wallet", -1)
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}: {ctx.guild.get_member(x['user'])}", f"**Wallet:** {x['wallet']}")
            data.append(to_append)

        pages = MenuPages(DefaultPageSource(f"Richest user in {ctx.guild.name}", data), ctx)
        await pages.start()

    @commands.command(help="Deposit your money into the bank", aliases=['dep'])
    async def deposit(self, ctx, amount=None):
        stats = await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
        if amount.lower() == "all":
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"bank": stats['wallet']}})
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$set": {"wallet": 0}})
            await ctx.message.add_reaction("✅")
            return
        amount = int(amount)
        if amount > stats['wallet']:
            return await ctx.send("You can't deposit more money than your wallet")
        elif amount <= 0:
            return await ctx.send("You can't send negative")
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": -amount}})
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"bank": amount}})
        await ctx.message.add_reaction("✅")

    @commands.command(help="Withdraw your money from the bank")
    async def withdraw(self, ctx, amount=None):
        stats = await self.economy.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
        if amount.lower() == "all":
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$set": {"bank": 0}})
            await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": stats['bank']}})
            await ctx.message.add_reaction("✅")
            return
        amount = int(amount)
        if amount > stats['bank']:
            return await ctx.send("You can't deposit more money than what's in your bank")
        elif amount <= 0:
            return await ctx.send("You can't send negative")
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": amount}})
        await self.economy.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"bank": -amount}})
        await ctx.message.add_reaction("✅")