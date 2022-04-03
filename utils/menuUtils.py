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


class MenuPages(discord.ui.View):
    def __init__(self, source: menus.PageSource):
        super().__init__(timeout=120.0)
        self._source = source
        self.ctx = None
        self.message = None
        self.current_page = 0

    async def _get_kwargs_from_page(self, page):
        value = await discord.utils.maybe_coroutine(self._source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}

    async def show_page(self, interaction, page_number):
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        if kwargs:
            if interaction.response.is_done():
                await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)

    async def show_checked_page(self, interaction, page_number):
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None:
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            pass

    async def start(self, ctx) -> None:
        self.ctx = ctx
        await self._source._prepare_once()
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self.message = await self.ctx.send(**kwargs, view=self)

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    async def on_error(self, error, item, interaction) -> None:
        await interaction.response.send_message(f"**Error:** {error}", ephemeral=True)

    async def interaction_check(self, interaction) -> bool:
        if interaction.user == self.ctx.author:
            return True
        await interaction.response.send_message("You can't use these buttons", ephemeral=True)
        return False

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.grey)
    async def first_page(self, interaction, button):
        await self.show_page(interaction, 0)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.grey)
    async def before_page(self, interaction, button):
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.grey)
    async def next_page(self, interaction, button):
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.grey)
    async def last_page(self, interaction, button):
        await self.show_page(interaction, self._source.get_max_pages() - 1)

    @discord.ui.button(emoji='🗑', style=discord.ButtonStyle.red)
    async def stop_page(self, interaction, button):
        await self.message.edit(view=None)
        self.stop()
