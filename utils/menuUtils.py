import discord
from discord.ext import menus


class ViewMenuPages(discord.ui.View, menus.MenuPages):
    def __init__(self, source):
        super().__init__(timeout=None)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None

    async def start(self, ctx, *, channel=None, wait=False):
        # We wont be using wait/channel, you can implement them yourself. This is to match the MenuPages signature.
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        """This method calls ListPageSource.format_page class"""
        value = await super()._get_kwargs_from_page(page)
        if 'view' not in value:
            value.update({'view': self})
        return value

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that the user of the button is the one who called the help command"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't use these buttons", ephemeral=True)
            return False
        else:
            return True

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.grey)
    async def first_page(self, button, interaction):
        await self.show_page(0)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.grey)
    async def before_page(self, button, interaction):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.grey)
    async def next_page(self, button, interaction):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.grey)
    async def last_page(self, button, interaction):
        await self.show_page(self._source.get_max_pages() - 1)

    @discord.ui.button(emoji='⏹', style=discord.ButtonStyle.grey)
    async def stop_page(self, button, interaction):
        for item in self.children:
            if isinstance(item, discord.Button):
                item.disabled = True
        await interaction.message.edit(view=self)
        self.stop()