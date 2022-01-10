import discord
from discord.ext import commands, menus
import random
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from cogs.economy.shopping_list import shop
from utils.menuUtils import MenuButtons
from main import config_var

cluster = AsyncIOMotorClient(config_var['mango_link'])
db = cluster["economy"]
cursor = db["users"]
nfts = db["nft"]


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


class NFTPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url="https://cdn.discordapp.com/attachments/900197917170737152/923101670207004723/NFT_Icon.png",
            name="NFT list")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


def is_account_available(ctx):
    account = cursor.find({"id": ctx.author.id})
    if account is None:
        return False
    else:
        return True


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def open_account(self, user):
        users = await cursor.find_one({"id": user.id})
        if users is None:
            insert = {"id": user.id, "job": "f", "FireCoin": 0, "wallet": 0, "bank": 0, "inventory": []}
            await cursor.insert_one(insert)
        else:
            return None

    @commands.command(help="See how much money you have", aliases=["bal"])
    async def balance(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        await self.open_account(user)

        check = await cursor.find_one({"id": user.id})
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

        await self.open_account(user)

        random_money = random.randint(1, 1000)
        await cursor.update_one({"id": user.id}, {"$inc": {"wallet": random_money}})
        await ctx.send(f"Someone gave you <:DHBuck:901485795410599988> {random_money}")

    @commands.command(help="we work for the right to work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @commands.guild_only()
    async def work(self, ctx):
        user = ctx.author
        await self.open_account(user)

        name = ["Tom", "John", "Jim", "Jack", "Henry", "Tim", "Lucas"]
        verbs = ["eat", "drink", "kicked", "paid", "build", "throw", "buy"]
        noun = ['a cat', 'the cashier', 'a ball', "an apple", 'a house', 'a bee', 'a cow', 'a computer']

        check = await cursor.find_one({"id": user.id})
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
    @commands.guild_only()
    async def buy(self, ctx, item_name, amount=1):
        user = ctx.author
        await self.open_account(user)

        check = await cursor.find_one({"id": user.id})

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
    @commands.guild_only()
    async def sell(self, ctx, item_name, amount=1):
        user = ctx.author

        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

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

                    is_amount_zero = await cursor.find_one(
                        {"id": user.id, "inventory.name": str(item_name), "inventory.amount": 0})
                    if is_amount_zero is not None:
                        await cursor.update_one({"id": user.id}, {"$pull": {"inventory": {"name": item_name}}})
                    await cursor.update_one({"id": user.id}, {"$inc": {"wallet": amounts * price}})
                    await ctx.send(f"Successfully sold {amount} {item_name} for {price}")
                    await asyncio.sleep(1)
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
            page = MenuButtons(InventoryPageSource(data))
            await page.start(ctx)

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
                await ctx.send(f"You just won <:DHBuck:901485795410599988> {amount}")
            else:
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -amount}})
                await ctx.send(f"You have lost <:DHBuck:901485795410599988> {amount}")

    @commands.command(help="Deposit your money into the bank", aliases=['dep'])
    @commands.guild_only()
    async def deposit(self, ctx, amount=1):
        user = ctx.author
        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

        if amount > check['wallet']:
            await ctx.send("You can't deposit more money than your wallet")
        else:
            await cursor.update_one({"id": user.id}, {"$inc": {"wallet": -amount}})
            await cursor.update_one({"id": user.id}, {"$inc": {"bank": amount}})
            await ctx.message.add_reaction("✅")

    @commands.command(help="Withdraw your money from the bank")
    @commands.guild_only()
    async def withdraw(self, ctx, amount=1):
        user = ctx.author
        await self.open_account(user)
        check = await cursor.find_one({"id": user.id})

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
                await user.send(f"**{ctx.author}** just gave you <:DHBuck:901485795410599988> {amount}")

    @commands.command(help="It's a crime to steal someone", aliases=['steal'])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    @commands.guild_only()
    async def rob(self, ctx, user: discord.Member = None, amount=1):
        await self.open_account(ctx.author)

        check1 = await cursor.find_one({"id": ctx.author.id})
        check2 = await cursor.find_one({"id": user.id})
        if check2 is None:
            await ctx.send("They don't have an economy account")
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

    @commands.group(invoke_without_command=True, case_insensitive=True, help="FireCoin commands")
    async def FireCoin(self, ctx):
        embed = discord.Embed(title="FireCoin", color=discord.Color.random())
        command = self.bot.get_command("FireCoin")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"FireCoin {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @FireCoin.command(help="Mine FireCoin")
    @commands.cooldown(1, 3600 * 2, commands.BucketType.user)
    @commands.guild_only()
    async def mine(self, ctx):
        await self.open_account(ctx.author)

        inventory_check = await cursor.find_one({"id": ctx.author.id, "inventory.name": "fireminer"})
        if inventory_check is None:
            await ctx.send("You need to buy a FireMiner to mine FireCoin")
        else:
            random_event = random.randint(1, 3)
            if random_event == 1:
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"FireCoin": 50}})
                await ctx.send("You tried to mine but it ran into some error so you receive <:FireCoin:920903065454903326> 50")
            elif random_event == 2:
                rand_amount = random.randint(1, 10000)
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"FireCoin": rand_amount}})
                await ctx.send(f"You just mined <:FireCoin:920903065454903326> {rand_amount}")
            else:
                await ctx.send("The machine is overloaded and crash, so you can't get more FireCoin")

    @commands.command(help="Buy FireCoin")
    async def fbuy(self, ctx, amount=1):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})
        cost = amount * 1000
        if check['wallet'] < cost:
            await ctx.send("Not enough money")
        else:
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"FireCoin": amount}})
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": -cost}})
            await ctx.send(f"You buy {amount} FireCoin for <:DHBuck:901485795410599988> {cost}")

    @FireCoin.command(help="Sell FireCoin")
    @commands.guild_only()
    async def sell(self, ctx, amount=1):
        await self.open_account(ctx.author)
        check = await cursor.find_one({"id": ctx.author.id})
        if check['FireCoin'] < amount:
            await ctx.send("You don't have enough FireCoin")
        else:
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"FireCoin": -amount}})
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": amount * 1000}})
            await ctx.send(f"You sold {amount} FireCoin and receive <:DHBuck:901485795410599988> {amount * 1000}")

    @FireCoin.command(help="Convert FireCoin to DHBuck")
    @commands.guild_only()
    async def convert(self, ctx, amount=1):
        await self.open_account(ctx.author)

        check = await cursor.find_one({"id": ctx.author.id})
        if check['FireCoin'] < amount:
            await ctx.send("Too much")
        else:
            await cursor.update_one({"id": ctx.author.id}, {"$inc": {"wallet": amount * 1000}})
            await ctx.send(f"Convert {amount} to {amount * 1000}")

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Nft are shit")
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
        questions = ["Enter Name: ", "Enter Image: "]
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
            await ctx.send(f"NFT {answers[0]} created for <:FireCoin:920903065454903326> {price}")

    @nft.command(help="Buy an nft")
    async def buy(self, ctx, *, name):
        await self.open_account(ctx.author)
        check = await nfts.find_one({"name": name})
        if check is None:
            await ctx.send("NFT do not exist. Also nft are CASE SENSITIVE")
        else:
            user = await cursor.find_one({"id": ctx.author.id})
            if user['FireCoin'] < check['price']:
                await ctx.send("You don't have enough FireCoin")
            else:
                og_owner = self.bot.get_user(check['owner'])
                await cursor.update_one({"id": ctx.author.id}, {"$inc": {"FireCoin": -check['price']}})
                await cursor.update_one({"id": og_owner.id}, {"$inc": {"FireCoin": check['price']}})
                await cursor.update_one({"id": og_owner.id}, {"$inc": {"price": random.randint(1, 1000)}})
                await nfts.update_one({"name": name}, {"$set": {"owner": ctx.author.id}})
                await og_owner.send(f"**{ctx.author}** just bought your nft name **{name}** and you receive <:FireCoin:920903065454903326> {check['price']}")

    @nft.command(help="View an nft")
    async def view(self, ctx, *, name):
        check = await nfts.find_one({"name": name})
        if check is None:
            await ctx.send("NFT do not exist. Also nft are CASE SENSITIVE")
        else:
            embed = discord.Embed(title=f"{check['name']}", description=f"**Price:** <:FireCoin:920903065454903326> {check['price']} \n**Owner:** {self.bot.get_user(check['owner'])}", color=discord.Color.from_rgb(225, 0, 92))
            embed.set_image(url=check['link'])
            await ctx.send(embed=embed)

    @nft.command(help="delete an nft")
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

    @nft.command(help="View all nfts")
    async def list(self, ctx):
        stats = nfts.find()
        data = []
        num = 0
        async for x in stats:
            num += 1
            to_append = (f"{num}. {x['name']}", f"**Price:** <:FireCoin:920903065454903326> {x['price']} **Owner:** {self.bot.get_user(x['owner'])}")
            data.append(to_append)

        pages = MenuButtons(NFTPageSource(data))
        await pages.start(ctx)