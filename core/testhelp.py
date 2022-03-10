import nextcord as discord
from nextcord.ext import commands, menus
from utils.menuUtils import MenuButtons


class HelpPageSource(menus.ListPageSource):
    def __init__(self, hdata, data):
        self.helpcommand = hdata
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        embed = discord.Embed(
            title=f"Use {self.helpcommand.context.clean_prefix}help [something] for more info on a command or category.",
            color=discord.Color.from_rgb(225, 0, 92)
        )
        embed.set_author(name=f"DangVietBot Help", icon_url="https://cdn.discordapp.com/avatars/875589545532485682/a5123a4fa15dad3beca44144d6749189.png?size=1024")
        embed.description = "\n".join([f"{name}: {value}" for name, value in entries])
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return f'{self.context.clean_prefix}{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='DangVietBot Commands',
                              description=f"{self.context.bot.description}",
                              color=discord.Color.from_rgb(225, 0, 92))
        for cog, command in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                value = '\u2002'.join(c.name for c in commands)
                if cog and cog.description:
                    value = '{0}\n{1}'.format(cog.description, value)

                embed.add_field(name=name, value=value)
        embed.set_footer(text=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Invite', url='https://bit.ly/3BJa6Nj'))
        view.add_item(discord.ui.Button(label='My server', url='https://discord.gg/cnydBRnHU9'))
        await self.get_destination().send(embed=embed, view=view)

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