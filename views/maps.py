import discord

from utils.enum import MapTypes


class MapTypeSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label=x, description="Map Type")
            for x in MapTypes.list()
        ]
        self.value_set = False

        super().__init__(
            placeholder="Choose map types...",
            min_values=1,
            max_values=sum(MapTypes.list()),
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.value_set = True
