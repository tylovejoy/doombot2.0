import discord
from utils.utilities import select_button_enable
from discord.ui import TextInput

from views.basic import ConfirmButton


class TournamentStartModal(discord.ui.Modal):
    def __init__(self, category: str) -> None:
        super().__init__("Tournament Submit Wizard")
        self.category = category
        self.add_item(TextInput(label="Map Code"))
        self.add_item(TextInput(label="Level Name"))
        self.add_item(TextInput(label="Map Creator"))
        self.code = None
        self.level = None
        self.creator = None

    async def callback(self, interaction: discord.Interaction):

        self.code = self.children[0].value
        self.level = self.children[1].value
        self.creator = self.children[2].value
        await interaction.response.send_message(
            f"{self.category} set.\nCode: {self.code}\nLevel: {self.level}\nCreator: {self.creator}",
            ephemeral=True,
        )


class TournamentStartView(discord.ui.View):
    """View for Tournament Start wizard."""

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.confirm_button = ConfirmButton()
        self.interaction = interaction
        self.ta_modal = None
        self.mc_modal = None
        self.hc_modal = None
        self.bo_modal = None

    @discord.ui.button(label="TA", style=discord.ButtonStyle.red)
    async def ta(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Time Attack button."""
        button.style = discord.ButtonStyle.green
        self.ta_modal = TournamentStartModal("Time Attack")
        await interaction.response.send_modal(self.ta_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="MC", style=discord.ButtonStyle.red)
    async def mc(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Mildcore button."""
        button.style = discord.ButtonStyle.green
        self.mc_modal = TournamentStartModal("Mildcore")
        await interaction.response.send_modal(self.mc_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="HC", style=discord.ButtonStyle.red)
    async def hc(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Hardcore button."""
        button.style = discord.ButtonStyle.green
        self.hc_modal = TournamentStartModal("Hardcore")
        await interaction.response.send_modal(self.hc_modal)
        await self.enable_accept_button()

    @discord.ui.button(label="BO", style=discord.ButtonStyle.red)
    async def bo(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Bonus button."""
        button.style = discord.ButtonStyle.green
        self.bo_modal = TournamentStartModal("Bonus")
        await interaction.response.send_modal(self.bo_modal)
        await self.enable_accept_button()

    async def enable_accept_button(self):
        """Enable confirm button when other buttons are pressed."""
        if len(self.children) != 5:
            self.add_item(self.confirm_button)
        await self.interaction.edit_original_message(view=self)


class TournamentCategoryView(discord.ui.View):
    """View for selecting tournament mentions."""

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.mentions = []
        self.interaction = interaction
        self.select = TournamentCategoriesSelect()
        self.add_item(self.select)

        self.confirm = ConfirmButton(row=1, disabled=True)
        self.add_item(self.confirm)


class TournamentCategoriesSelect(discord.ui.Select):
    """Tournament categories."""

    def __init__(self):
        super().__init__(
            placeholder="Choose which roles to be mentioned...",
            min_values=0,
            max_values=6,
            options=[
                discord.SelectOption(label="Time Attack", value="Time Attack"),
                discord.SelectOption(label="Mildcore", value="Mildcore"),
                discord.SelectOption(label="Hardcore", value="Hardcore"),
                discord.SelectOption(label="Bonus", value="Bonus"),
                discord.SelectOption(label="Trifecta", value="Trifecta"),
                discord.SelectOption(label="Bracket", value="Bracket"),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        """Callback for tournament categories dropdown."""
        self.view.mentions = self.values
        await select_button_enable(self.view, self)
