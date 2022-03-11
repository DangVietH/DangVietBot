import nextcord as discord
from nextcord.ext import commands, menus
from utils.menuUtils import MenuButtons

# menu help base on https://github.com/DenverCoder1/dev-pro-tips-bot/blob/main/cogs/help/help_command.py


class HelpPageSource(menus.ListPageSource):
    def __init__(self, hdata, data):
        self._help_command = hdata
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        """
        Returns an embed containing the entries for the current page
        """
        prefix = self._help_command.context.clean_prefix
        invoked_with = self._help_command.invoked_with
        embed = discord.Embed(title="Bot Commands", color=discord.Color.from_rgb(225, 0, 92))
        embed.description = f'Use {prefix}{invoked_with}help [something] for more info on a command or category'
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=True)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return f'- {self.context.clean_prefix}{command.qualified_name} : {command.signature}'

    async def send_bot_help(self, mapping):
        data = []

        for cog, command in mapping.items():
            name = "No Category" if cog is None else cog.qualified_name
            filtered = await self.filter_commands(command, sort=True)
            if filtered:
                value = "\u2002".join(
                    self.get_command_signature(c) for c in filtered)
                if cog and cog.description:
                    value = f"\n{value}"
                data.append((name, value))

        # create a pagination menu that paginates the fields
        pages = MenuButtons(
            ctx=self.context,
            source=HelpPageSource(self, data),
            disable_buttons_after=True
        )
        await pages.start(self.context)

    async def send_cog_help(self, cog_):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog_), color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')

        filtered = await self.filter_commands(cog_.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=command.name,
                            value=f"```{command.short_doc}```" or 'No description Provided', inline=False)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=command.name,
                                value=f"```{command.short_doc}```" or 'No description Provided', inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.name, color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')
        if command.help:
            embed.add_field(name="Description", value=f"```{command.help}```", inline=False)
        if command.aliases:
            embed.add_field(name="Aliases", value=f"```{command.aliases}```", inline=False)
        embed.add_field(name="Usage", value=f"```{self.get_command_signature(command)}```", inline=False)
        await self.get_destination().send(embed=embed)