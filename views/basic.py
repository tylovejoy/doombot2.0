import logging

import discord


logger = logging.getLogger()


class ConfirmButton(discord.ui.Button):
    """Confirmation button."""

    def __init__(self, row=0, disabled=False):
        """Init button component."""
        super().__init__(
            emoji="✔️", style=discord.ButtonStyle.green, row=row, disabled=disabled
        )
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        """Callback for confirm button."""
        self.value = True
        self.view.clear_items()
        self.view.stop()


class ConfirmView(discord.ui.View):
    """View for a confirmation button."""

    def __init__(self):
        super().__init__(timeout=None)
        self.confirm = ConfirmButton()
        self.add_item(self.confirm)
