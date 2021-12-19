import discord
from discord.ext import commands, menus
import random
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
from cogs.economy.shopping_list import shop
from discord.ext.commands.errors import CheckFailure

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["economy"]
cursor = db["users"]

NO_ACCOUNT = "You don't have an economy account. Please use the create_account command to create one"


class MenuButtons(discord.ui.View, menus.MenuPages):
    def __init__(self, source):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None

    async def start(self, ctx, *, channel=None, wait=False):
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        value = await super()._get_kwargs_from_page(page)
        if 'view' not in value:
            value.update({'view': self})
        return value

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.green)
    async def first_page(self, button, interaction):
        await self.show_page(0)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.green)
    async def previous_page(self, button, interaction):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(emoji='⏹', style=discord.ButtonStyle.green)
    async def on_stop(self, button, interaction):
        self.stop()

    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.green)
    async def next_page(self, button, interaction):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.green)
    async def last_page(self, button, interaction):
        max_pages = self._source.get_max_pages()
        last_page = max(max_pages - 1, 0)
        await self.show_page(last_page)


class InventoryPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url=menu.ctx.author.avatar.url,
            name=f"{menu.ctx.author} Inventory")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class GuildRichPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green(),
                              description="Base by wallet")
        embed.set_author(
            icon_url=menu.ctx.author.guild.icon.url,
            name=f"Riches user in {menu.ctx.author.guild.name}")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class GlobalRichPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green(), description="Base by wallet")
        embed.set_author(
            icon_url="https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif",
            name="Riches users in the world")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class ShopPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url="https://cdn.discordapp.com/attachments/900197917170737152/921035393456042004/shop.png",
            name="Shop")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Create your economy account")
    async def create_account(self, ctx):
        check = await cursor.find_one({"id": ctx.author.id})
        if check is None:
            insert = {"id": ctx.author.id, "job": "f", "FireCoin": 0, "wallet": 0, "bank": 0, "inventory": []}
            await cursor.insert_one(insert)
            await ctx.send("Done, your global economy account has been created.")
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
            embed = discord.Embed(description=f"**Total:** <:DHBuck:901485795410599988> {balance}",
                                  color=discord.Color.blue())
            embed.set_author(
                icon_url=user.avatar.url,
                name=f"{user} balance")
            embed.add_field(name="Wallet", value=f"<:DHBuck:901485795410599988> {wallet}", inline=False)
            embed.add_field(name="Bank", value=f"<:DHBuck:901485795410599988> {bank}", inline=False)
            embed.add_field(name="FireCoin", value=f"<:FireCoin:920903065454903326> {check['FireCoin']}", inline=False)
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

        pages = MenuButtons(GuildRichPageSource(data))
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

        pages = MenuButtons(GlobalRichPageSource(data))
        await pages.start(ctx)

    @commands.command(help="Beg some money")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    @commands.guild_only()
    async def beg(self, ctx):
        user = ctx.author
        check = await cursor.find_one({"id": user.id})
        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
            random_money = random.randint(1, 1000)
            await cursor.update_one({"id": user.id}, {"$inc": {"wallet": random_money}})
            await ctx.send(f"Someone gave you <:DHBuck:901485795410599988> {random_money}")

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @commands.guild_only()
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
            await ctx.send(''.join(emojis))
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
                    await cursor.update_one({"id": user.id}, {"$inc": {"wallet": random_money}})
                    embed = discord.Embed(title="GOOD JOB",
                                          description=f"Your receive <:DHBuck:901485795410599988> {random_money} for successfully converting it to a text",
                                          color=discord.Color.green())
                    await message.reply(embed=embed)
                else:
                    low_money = random.randint(10, 100)
                    await cursor.update_one({"id": user.id}, {"$inc": {"wallet": low_money}})
                    embed = discord.Embed(title="🤦 BAD WORK 🤦",
                                          description=f"You didn't answer correctly. You only receive <:DHBuck:901485795410599988> {low_money}",
                                          color=discord.Color.red())
                    await message.reply(embed=embed)

    @commands.command(help="Shopping list", aliases=['sl'])
    async def shop(self, ctx):
        data = []
        for item in shop:
            name = item["name"]
            price = item["price"]
            description = item["description"]
            to_append = (f"{name} | <:DHBuck:901485795410599988> {price}", f"{description}")
            data.append(to_append)

        page = MenuButtons(ShopPageSource(data))
        await page.start(ctx)

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
                await cursor.update_one({"id": user.id}, {"$inc": {"wallet": -cost}})
                await ctx.send(f"You just brought {amount} {item_name} that cost <:DHBuck:901485795410599988>  {cost}")

    @commands.command(help="Sell your items")
    @commands.is_owner()
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
                await ctx.send("That item wasn't in your inventory")

            for item in check['inventory']:
                if item['name'].lower() == item_name:
                    amounts = item['amount']
                    if amounts < amount:
                        await ctx.send("Too much")
                    else:
                        await cursor.update_one({"id": user.id, "inventory.name": str(item_name)},
                                                {"$inc": {"inventory.$.amount": -amount}})
                        if item['amount'] == 0:
                            await cursor.update_one({"id": user.id},
                                                    {"$pull": {
                                                        "inventory": {"name": item_name}}})
                        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": amounts * price}})
                        await ctx.send(f"Successfully sold {amount} {item_name} for {price}")
                    break

    @commands.command(help="See your items", aliases=["bag"])
    async def inventory(self, ctx):
        check = await cursor.find_one({"id": ctx.author.id})
        if check is None:
            await ctx.send(NO_ACCOUNT)
        else:
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
                page = MenuButtons(InventoryPageSource(data))
                await page.start(ctx)

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
                anti_rob_1 = await cursor.find_one({"id": user.id, "inventory.name": "robber_shield"})
                if anti_rob_1 is not None:
                    author_update = check1['wallet'] + 10
                    user_update = check2['wallet'] - 10
                    await cursor.update_one({"id": ctx.author.id}, {"$set": {"bank": author_update}})
                    await cursor.update_one({"id": user.id}, {"$set": {"bank": user_update}})
                    await ctx.send(f"You tried to rob him but you only got <:DHBuck:901485795410599988> 10")

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
