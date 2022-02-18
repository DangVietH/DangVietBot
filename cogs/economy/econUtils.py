import nextcord as discord
from nextcord.ext import menus

shop_png = "https://cdn.discordapp.com/attachments/900197917170737152/921035393456042004/shop.png"
nft_png = "https://cdn.discordapp.com/attachments/900197917170737152/923101670207004723/NFT_Icon.png"


class InventoryPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(
            icon_url=menu.ctx.author.avatar.url,
            name=f"{menu.ctx.author} Inventory")
        for entry in entries: embed.add_field(name=entry[0], value=entry[1])
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
        for entry in entries: embed.add_field(name=entry[0], value=entry[1], inline=False)
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
        for entry in entries: embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class ShopPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green(), title="SHOP")
        for entry in entries: embed.add_field(name=entry[0], value=entry[1])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class NFTPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green(), title="PLZ SCREENSHOT THEM")
        for entry in entries: embed.add_field(name=entry[0], value=entry[1])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        embed.set_thumbnail(url=nft_png)
        return embed
