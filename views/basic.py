import logging

import discord


logger = logging.getLogger()


class BaseView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author

    async def interaction_check(self, item, interaction: discord.Interaction):
        if self.author == interaction.user:
            return True
        else:
            await interaction.response.send_message(
                "You can't interact with these buttons as you weren't the one using the command.",
                ephemeral=True,
            )
            return False


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
