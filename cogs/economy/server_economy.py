import discord
from discord.ext import commands, menus
from motor.motor_asyncio import AsyncIOMotorClient
import os
import random

cluster = AsyncIOMotorClient(os.environ.get("mango_link"))
db = cluster["economy"]
serverSetup = db["server"]
econUser = db['server_user']


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


class ShopPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url="https://cdn.discordapp.com/attachments/900197917170737152/921035393456042004/shop.png",
            name=f"{menu.ctx.author.guild.name} Shop")
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class ServerEconomy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def server_econ_create(self, guild):
        check = await serverSetup.find_one({"id": guild.id})
        if check is None:
            insert = {"id": guild.id, "shop": [], "rob": "True", "emoji": "<:DHBuck:901485795410599988>", "starting_wallet": 0, "role": [], "rolenum": []}
            await serverSetup.insert_one(insert)

    async def open_account(self, user):
        users = await econUser.find_one({"guild": user.guild.id, "user": user.id})
        servercheck = await serverSetup.find_one({"id": user.guild.id})
        if users is None:
            insert = {"guild": user.guild.id, "user": user.id, "wallet": int(servercheck['starting_wallet']), "bank": 0, "inventory": []}
            await econUser.insert_one(insert)

    @commands.group(invoke_without_command=True, case_insensitive=True, help="Server economy commands")
    async def se(self, ctx):
        embed = discord.Embed(title="Server economy", color=discord.Color.random())
        command = self.bot.get_command("se")
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                embed.add_field(name=f"se {subcommand.name}", value=f"```{subcommand.help}```", inline=False)
        await ctx.send(embed=embed)

    @se.command(help="Set server economy emoji")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def emote(self, ctx, *, emoji: str):
        await self.server_econ_create(ctx.guild)

        await serverSetup.update_one({"id": ctx.guild.id}, {"$set": {"emoji": emoji}})
        await ctx.send(f"Economy emoji is now {emoji}")

    @se.command(help="Server store")
    @commands.guild_only()
    async def shop(self, ctx):
        await self.server_econ_create(ctx.guild)

        check = await serverSetup.find_one({"id": ctx.guild.id})
        items = check['shop']
        if len(items) < 1:
            await ctx.send("There's nothing in the shop! Do create_item")
        else:
            data = []
            for item in items:
                name = item["name"]
                price = item["price"]
                description = item["description"]
                to_append = (f"{name} | {check['emoji']} {price}", f"{description}")
                data.append(to_append)

            pages = MenuButtons(ShopPageSource(data))
            await pages.start(ctx)

    @se.command(help="Server store")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def create_item(self, ctx, name: str, price: int, stock=None, role_required=None, give_role=None, remove_role=None, money_in_wallet=0, *, description="I dunno"):
        await self.server_econ_create(ctx.guild)

        inventory_check = await serverSetup.find_one({"id": ctx.guild.id, "shop.name": name})
        if inventory_check is not None:
            await ctx.send("Item already exist")
        else:
            await serverSetup.update_one({"id": ctx.guild.id}, {"$push": {"shop": {"name": name, "price": price, "description": description, "stock": stock, "role_required": role_required, "give_role": give_role, "remove_role": remove_role, "money_in_wallet": money_in_wallet}}})
            await ctx.send("Item added")

    @se.command(help="View your server balance")
    @commands.guild_only()
    async def bal(self, ctx):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})
        severSys = await serverSetup.find_one({"id": ctx.guild.id})

        wallet = check['wallet']
        bank = check['bank']
        balance = wallet + bank
        embed = discord.Embed(description=f"**Total:** {severSys['emoji']} {balance}",
                              color=discord.Color.blue())
        embed.set_author(
            icon_url=ctx.author.avatar.url,
            name=f"{ctx.author} balance")
        embed.add_field(name="Wallet", value=f"{severSys['emoji']} {wallet}", inline=False)
        embed.add_field(name="Bank", value=f"{severSys['emoji']} {bank}", inline=False)
        await ctx.send(embed=embed)

    @se.command(help="Deposit your money into the bank", aliases=['dep'])
    @commands.guild_only()
    async def deposit(self, ctx, amount=1):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})

        if amount > check['wallet']:
            await ctx.send("You can't deposit more money than your wallet")
        else:
            await econUser.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": -amount}})
            await econUser.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"bank": amount}})
            await ctx.message.add_reaction("✅")

    @se.command(help="Withdraw your money from the bank")
    @commands.guild_only()
    async def withdraw(self, ctx, amount=1):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        check = await econUser.find_one({"guild": ctx.guild.id, "user": ctx.author.id})

        if amount > check['bank']:
            await ctx.send("You can't deposit more money than your bank")
        else:
            await econUser.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": amount}})
            await econUser.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"bank": -amount}})
            await ctx.message.add_reaction("✅")

    @se.command(help="Beg money")
    @commands.guild_only()
    @commands.cooldown(1, 7200, commands.BucketType.member)
    async def beg(self, ctx):
        await self.server_econ_create(ctx.guild)
        await self.open_account(ctx.author)

        severSys = await serverSetup.find_one({"id": ctx.guild.id})

        random_money = random.randint(1, 1000)
        await econUser.update_one({"guild": ctx.guild.id, "user": ctx.author.id}, {"$inc": {"wallet": random_money}})
        await ctx.send(f"Someone gave you {severSys['emoji']} {random_money}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        for member in guild.members:
            if not member.bot:
                result = await econUser.find_one({"guild": guild.id, "user": member.id})
                if result is not None:
                    await econUser.delete_one({"guild": guild.id, "user": member.id})
        check = await serverSetup.find_one({"id": guild.id})
        if check is not None:
            await serverSetup.delete_one({"id": guild.id})

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not member.bot:
            result = await econUser.find_one({"guild": member.guild.id, "user": member.id})
            if result is not None:
                await econUser.delete_one({"guild": member.guild.id, "user": member.id})