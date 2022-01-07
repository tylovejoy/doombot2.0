import discord

from utils.enums import MapTypes
from views.basic import ConfirmButton


class MapTypeSelect(discord.ui.Select):
    """A select dropdown of map types."""

    def __init__(self):
        """Init dropdown component."""
        options = [discord.SelectOption(label=x) for x in MapTypes.list()]
        self.value_set = False
        super().__init__(
            placeholder="Choose map types...",
            min_values=0,
            max_values=len(MapTypes.list()),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback for map types component."""
        print(self.values)
        if len(self.values):
            self.view.confirm.disabled = False
        else:
            self.view.confirm.disabled = True
        for x in self.options:
            if x.label in self.values:
                x.default = True
            else:
                x.default = False
        await self.view.interaction.edit_original_message(view=self.view)



class MapSubmitView(discord.ui.View):
    """View for map submissions."""

    def __init__(self, interaction: discord.Interaction, timeout=None, confirm_disabled=True):
        """Init view."""
        super().__init__(timeout=timeout)
        self.interaction = interaction

        self.select_menu = MapTypeSelect()
        self.add_item(self.select_menu)

        self.confirm = ConfirmButton(row=1, disabled=confirm_disabled)
        self.add_item(self.confirm)
