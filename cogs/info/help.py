import discord
from discord.ext import commands, menus
import datetime
from utils.menuUtils import MenuPages


class CogPageSource(menus.ListPageSource):
    def __init__(self, title, data):
        self.title = title
        super().__init__(data, per_page=5)

    async def format_page(self, menu, entries):
        embed = discord.Embed(
            color=menu.ctx.bot.embed_color,
            title=self.title,
            timestamp=datetime.datetime.utcnow(),
            description="<> = required argument | [] = optional argument"
        )
        for entry in entries:
            embed.add_field(name=entry[0], value=entry[1], inline=False)
        embed.set_footer(text=f'Page {menu.current_page + 1}/{self.get_max_pages()}')
        return embed


class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return f'{self.context.clean_prefix}{command.qualified_name} {command.signature}'

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Sorry but that command does not exist.")

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='DangVietBot Categories',
                              description=f"{self.context.bot.description}",
                              color=self.context.bot.embed_color)
        for cog, command in mapping.items():
            command_signatures = [self.get_command_signature(c) for c in command]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                if cog_name != "Jishaku":
                    embed.add_field(name=cog_name, value=f"Commands: {len(command)}")
        embed.set_footer(
            text=f'Use {self.context.clean_prefix}help [arg] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Invite',
                                        url=self.context.bot.invite))
        view.add_item(discord.ui.Button(label='My server', url='https://discord.gg/cnydBRnHU9'))
        await self.get_destination().send(embed=embed, view=view)

    async def send_cog_help(self, cog_):
        data = []
        filtered = await self.filter_commands(cog_.get_commands(), sort=True)
        for command in filtered:
            data.append((f"- {command.name}", f"{self.get_command_signature(command)}\n`{command.short_doc}`"))

        page = MenuPages(CogPageSource(f"{cog_.qualified_name} Commands", data))
        await page.start(self.context)

    async def send_group_help(self, group):
        data = []
        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                data.append((f"- {command.name}", f"{self.get_command_signature(command)}\n`{command.short_doc}`"))

        page = MenuPages(CogPageSource(f"{group.qualified_name} Commands", data))
        await page.start(self.context)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.name, color=discord.Color.from_rgb(225, 0, 92),
                              description=f'Use {self.context.clean_prefix}help [something] for more info on a command or category. \nExample: {self.context.clean_prefix}help Economy')
        if command.help:
            embed.add_field(name="Description", value=f"```{command.help}```", inline=False)
        if command.aliases:
            embed.add_field(name="Aliases", value=f"```{command.aliases}```", inline=False)
        embed.add_field(name="Usage", value=f"```{self.get_command_signature(command)}```", inline=False)
        await self.get_destination().send(embed=embed)
