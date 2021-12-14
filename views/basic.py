import discord
from discord import Interaction


class ConfirmButton(discord.ui.Button):

    """Confirmation button."""

    def __init__(self, row=0, disabled=False):
        """Init button component."""
        super().__init__(
            label="Accept", style=discord.ButtonStyle.green, row=row, disabled=disabled
        )
        self.value = None

    async def callback(self, interaction: Interaction):
        """Callback for confirm button."""
        self.value = True
        self.view.stop()
