import discord

from views import ConfirmButton


class TournamentCategorySelect(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.mentions = []
        self.confirm = ConfirmButton(row=1, disabled=True)
        self.add_item(self.confirm)

    @discord.ui.select(
        options=[
            discord.SelectOption(label="Time Attack", value="ta"),
            discord.SelectOption(label="Mildcore", value="mc"),
            discord.SelectOption(label="Hardcore", value="hc"),
            discord.SelectOption(label="Bonus", value="bo"),
            discord.SelectOption(label="Trifecta", value="tr"),
            discord.SelectOption(label="Bracket", value="br"),
        ],
        placeholder="Choose which roles to be mentioned...",
        min_values=1,
        max_values=6,
    )
    async def callback(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        self.mentions = select.values
        self.confirm.disabled = False
        await interaction.edit_original_message(view=self)


class TournamentCategories(discord.ui.Select):
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
        """Callback for map types component."""
        self.view.confirm.disabled = False
