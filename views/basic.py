import logging
from typing import List

import discord

from database.documents import Guide

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

    async def start(
        self,
        interaction: discord.Interaction,
        first_msg: str,
        second_msg: str,
        embed: discord.Embed = discord.Embed.Empty,
    ) -> bool:
        await interaction.edit_original_message(
            content=first_msg,
            view=self,
            embed=embed,
        )
        await self.wait()

        if not self.confirm.value:
            return False

        await interaction.edit_original_message(
            content=second_msg,
            view=self,
            embed=embed,
        )
        return True


number_emoji = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟",
}

class GuideDeleteView(discord.ui.View):
    def __init__(self, guides: List[str]):
        super().__init__(timeout=None)
        self.confirm = ConfirmButton(row=1)
        self.dropdown = discord.ui.Select()
        for i, guide in enumerate(guides, 1):
            if i == 11:
                break
            self.dropdown.add_option(
                label=number_emoji[i] + guide,
                value=i - 1,
            )
        self.add_item(self.dropdown)
        self.add_item(self.confirm)
