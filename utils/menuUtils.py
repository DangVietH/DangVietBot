import nextcord as discord
from nextcord.ext import menus, commands


class MenuButtons(menus.ButtonMenuPages):
    FIRST_PAGE = "⏪"
    PREVIOUS_PAGE = "◀️"
    STOP = "⏹"
    NEXT_PAGE = "▶️"
    LAST_PAGE = "⏩"

    def __init__(self, ctx: commands.Context, **kwargs):
        super().__init__(**kwargs)
        self._ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure that the user of the button is the one who called the help command"""
        if interaction.user != self._ctx.author:
            await interaction.response.send_message("These buttons are not for you idiot", ephemeral=True)
            return False
        else:
            return True