import discord

from views import ConfirmButton


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
