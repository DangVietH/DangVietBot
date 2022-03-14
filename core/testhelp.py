from typing import Optional, Set
import discord
from discord.ext import commands

# code base on https://github.com/DenverCoder1/Tutorial-Discord-Bot/blob/main/modules/help/help_command.py


class HelpDropdown(discord.ui.Select):
    def __init__(self, help_command: "CustomHelp", options: list[discord.SelectOption]):
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)
        self._help_command = help_command

    async def callback(self, interaction: discord.Interaction):
        embed = (
            await self._help_command.cog_help_embed(self._help_command.context.bot.get_cog(self.values[0]))
            if self.values[0] != self.options[0].value
            else await self._help_command.bot_help_embed(self._help_command.get_bot_mapping())
        )
        await interaction.response.edit_message(embed=embed)


class HelpView(discord.ui.View):
    def __init__(self, help_command: "CustomHelp", options: list[discord.SelectOption], *, timeout: Optional[float] = 120.0):
        super().__init__(timeout=timeout)
        self.add_item(HelpDropdown(help_command, options))
        self._help_command = help_command

    async def on_timeout(self):
        # remove dropdown from message on timeout
        self.clear_items()
        await self._help_command.response.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self._help_command.context.author == interaction.user


class CustomHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def _cog_select_options(self) -> list[discord.SelectOption]:
        options: list[discord.SelectOption] = []
        options.append(discord.SelectOption(
            label="Home",
            emoji="🏠",
            description="The Main Menu",
        ))

        for cog, command_set in self.get_bot_mapping().items():
            filtered = await self.filter_commands(command_set, sort=True)
            if not filtered:
                continue
            emoji = getattr(cog, "COG_EMOJI", None)
            options.append(discord.SelectOption(
                label=cog.qualified_name if cog else "No Category",
                emoji=emoji,
                description=cog.description[:100] if cog and cog.description else "No description provided"
            ))

        return options

    async def _help_embed(
            self, title: str, description: Optional[str] = None, mapping: Optional[str] = None,
            command_set: Optional[Set[commands.Command]] = None, set_author: bool = False
    ) -> discord.Embed:
        embed = discord.Embed(title=title, color=discord.Color.from_rgb(225, 0, 92))
        if description:
            embed.description = description
        if set_author:
            avatar = self.context.bot.user.avatar or self.context.bot.user.default_avatar
            embed.set_author(name=self.context.bot.user.name, icon_url=avatar.url)
        if command_set:
            # show help about all commands in the set
            filtered = await self.filter_commands(command_set, sort=True)
            for command in filtered:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.short_doc or "...",
                    inline=False
                )
        elif mapping:
            embed.add_field(name="List of categories:", value=f"""
Music

Economy

Fun

Leveling

LevelUtils

Admin

ModSet

Giveaway

Owner

Dev

Setup

Info

Misc

BotUtils

Tags
            """)
        return embed

    async def bot_help_embed(self, mapping: dict) -> discord.Embed:
        return await self._help_embed(
            title="Bot Commands",
            description=self.context.bot.description,
            mapping=mapping,
            set_author=True,
        )

    async def send_bot_help(self, mapping: dict):
        embed = await self.bot_help_embed(mapping)
        options = await self._cog_select_options()
        self.response = await self.get_destination().send(embed=embed, view=HelpView(self, options))

    async def send_command_help(self, command: commands.Command):
        emoji = getattr(command.cog, "COG_EMOJI", None)
        embed = await self._help_embed(
            title=f"{emoji} {command.qualified_name}" if emoji else command.qualified_name,
            description=command.help,
            command_set=command.commands if isinstance(command, commands.Group) else None
        )
        await self.get_destination().send(embed=embed)

    async def cog_help_embed(self, cog: Optional[commands.Cog]) -> discord.Embed:
        if cog is None:
            return await self._help_embed(
                title=f"No category",
                command_set=self.get_bot_mapping()[None]
            )
        emoji = getattr(cog, "COG_EMOJI", None)
        return await self._help_embed(
            title=f"{emoji} {cog.qualified_name}" if emoji else cog.qualified_name,
            description=cog.description,
            command_set=cog.get_commands()
        )

    async def send_cog_help(self, cog: commands.Cog):
        embed = await self.cog_help_embed(cog)
        await self.get_destination().send(embed=embed)

    # Use the same function as command help for group help
    send_group_help = send_command_help