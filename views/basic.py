import discord
from discord import Interaction


class ConfirmButton(discord.ui.Button):
    def __init__(self, row=0, disabled=False):
        super().__init__(
            label="Accept", style=discord.ButtonStyle.green, row=row, disabled=disabled
        )
        self.value = None

    async def callback(self, interaction: Interaction):
        self.value = True
        self.view.stop()
