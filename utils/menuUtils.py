import discord
from discord.ext import menus


class MenuButtons(discord.ui.View, menus.MenuPages):
    def __init__(self, source):
        super().__init__(timeout=None)
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
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("These buttons are not for you idiot", ephemeral=True)
            return False
        else:
            return True

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