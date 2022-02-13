from typing import Literal

import discord

from slash.parents import CreateParent
from utils.constants import GUILD_ID


class CreateEvent(
    discord.SlashCommand, guilds=[GUILD_ID], name="event", parent=CreateParent
):
    """Create an event."""

    event_type: Literal["Movie", "Game"] = discord.Option(
        description="What type of event is it?",
    )

    schedule_start: str = discord.Option(
        description="When should the event start?",
    )

    async def callback(self) -> None:
        # TODO: wait for implementation of scheduled events
        pass
