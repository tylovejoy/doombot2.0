import discord
from discord.interactions import Interaction

from utils.enum import MapTypes


class MapTypeSelect(discord.ui.Select):
    def __init__(self):

        options = [discord.SelectOption(label=x) for x in MapTypes.list()]
        self.value_set = False

        super().__init__(
            placeholder="Choose map types...",
            min_values=1,
            max_values=len(MapTypes.list()),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.confirm.disabled = False


class ConfirmButton(discord.ui.Button):
    def __init__(self, row=0, disabled=False):
        super().__init__(
            label="Accept", style=discord.ButtonStyle.green, row=row, disabled=disabled
        )
        self.value = None

    async def callback(self, interaction: Interaction):
        self.value = True
        self.view.stop()


class MapSubmitView(discord.ui.View):
    def __init__(self, *, timeout=None, confirm_disabled=True):
        super().__init__(timeout=timeout)
        self.select_menu = MapTypeSelect()
        self.add_item(self.select_menu)

        self.confirm = ConfirmButton(row=1, disabled=confirm_disabled)
        self.add_item(self.confirm)
