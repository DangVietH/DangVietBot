import discord
from discord.ext import menus
import datetime


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
        await ctx.message.add_reaction("✅")

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

    @discord.ui.button(emoji='🗑', style=discord.ButtonStyle.red)
    async def stop_page(self, button, interaction):
        self.stop()
        await self.message.delete()


class DefaultPageSource(menus.ListPageSource):
    def __init__(self, title, data):
        self.title = title
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        embed = discord.Embed(color=discord.Color.green(), title=self.title, timestamp=datetime.datetime.utcnow())
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed