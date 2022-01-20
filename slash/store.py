from typing import Literal
import discord

from utils.constants import GUILD_ID

class OpenStore(discord.SlashCommand, guilds=[GUILD_ID], name="store"):
    """View the XP store."""

    category: Literal["Emotes", "Roles"] = discord.Option(
        "Which category in the store would you like to browse?"
    )

    async def callback(self) -> None:
        if self.category == "Emotes":
            # Shop Emotes View
            return

        if self.category == "Roles":
            # Shop Roles View
            return
            