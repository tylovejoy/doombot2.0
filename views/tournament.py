from logging import disable
import discord
from discord.enums import ButtonStyle
from discord.interactions import Interaction
from discord.partial_emoji import PartialEmoji

from views.basic import ConfirmButton


class TournamentStartView(discord.ui.View):
    """View for Tournament Start wizard."""

    def __init__(self, interaction: Interaction):
        super().__init__(timeout=None)
        self.confirm_button = ConfirmButton()
        self.interaction = interaction

    @discord.ui.button(label="TA", style=ButtonStyle.red)
    async def ta(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Time Attack button."""
        await self.enable_accept_button()

    @discord.ui.button(label="MC", style=ButtonStyle.red)
    async def mc(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Mildcore button."""
        await self.enable_accept_button()

    @discord.ui.button(label="HC", style=ButtonStyle.red)
    async def hc(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Hardcore button."""
        await self.enable_accept_button()

    @discord.ui.button(label="BO", style=ButtonStyle.red)
    async def bo(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Bonus button."""
        await self.enable_accept_button()

    async def enable_accept_button(self):
        """Enable confirm button when other buttons are pressed."""
        if len(self.children) != 5:
            self.add_item(self.confirm_button)
            await self.interaction.edit_original_message(view=self)


class TournamentCategoryView(discord.ui.View):
    """View for selecting tournament mentions."""

    def __init__(self):
        super().__init__()
        self.mentions = []
        self.select = TournamentCategoriesSelect()
        self.add_item(self.select)
        self.confirm = ConfirmButton(row=1, disabled=True)
        self.add_item(self.confirm)


class TournamentCategoriesSelect(discord.ui.Select):
    """Tournament categories."""

    def __init__(self):
        super().__init__(
            placeholder="Choose which roles to be mentioned...",
            min_values=1,
            max_values=6,
            options=[
                discord.SelectOption(label="Time Attack", value="ta"),
                discord.SelectOption(label="Mildcore", value="mc"),
                discord.SelectOption(label="Hardcore", value="hc"),
                discord.SelectOption(label="Bonus", value="bo"),
                discord.SelectOption(label="Trifecta", value="tr"),
                discord.SelectOption(label="Bracket", value="br"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback for tournament categories dropdown."""
        self.view.mentions = self.values
        self.confirm.disabled = False
        await interaction.edit_original_message(view=self.view)
