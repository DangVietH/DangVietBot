import discord
from discord.ext import menus
import datetime


class DefaultPageSource(menus.ListPageSource):
    def __init__(self, title, data):
        self.title = title
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=0x2F3136, title=self.title, timestamp=datetime.datetime.utcnow())
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class SecondPageSource(menus.ListPageSource):
    def __init__(self, title, data):
        self.title = title
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=0x2F3136)
        embed.description = "\n".join([f"{name}: {value}" for name, value in entries])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class MenuPages(discord.ui.View, menus.MenuPages):
    """Custom MenuPages with buttons"""
    def __init__(self, source):
        super().__init__(timeout=120.0)
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

    async def interaction_check(self, interaction) -> bool:
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message('This pagination menu cannot be controlled by you, sorry!', ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def on_error(self, error, item, interaction) -> None:
        await interaction.response.send_message(
            f"An error occurred, sorry: {error}", ephemeral=True
        )

    async def show_interation_page(self, interaction, page):
        self.current_page = page
        if interaction.response.is_done():
            await self.show_page(page)

    async def show_check_interation_page(self, interaction, page):
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                await self.show_interation_page(interaction, page)
            elif max_pages > page >= 0:
                await self.show_interation_page(interaction, page)
        except IndexError:
            pass

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.grey)
    async def first_page(self, button, interaction):
        await self.show_interation_page(interaction, 0)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.grey)
    async def before_page(self, button, interaction):
        await self.show_check_interation_page(interaction, self.current_page - 1)

    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.grey)
    async def next_page(self, button, interaction):
        await self.show_check_interation_page(interaction, self.current_page + 1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.grey)
    async def last_page(self, button, interaction):
        await self.show_interation_page(interaction, self._source.get_max_pages() - 1)

    @discord.ui.button(emoji='🗑', style=discord.ButtonStyle.red)
    async def stop_page(self, button, interaction):
        await self.message.edit(view=None)
        self.stop()
