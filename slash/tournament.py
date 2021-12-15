from datetime import datetime
from logging import getLogger
from typing import Optional

import discord
from database.tournament import (
    TournamentMaps,
    TournamentCategories,
    Tournament,
    TournamentRecords,
    TournamentMissions,
)

from slash.parents import TournamentParent, TournamentSubmitParent
from utils.constants import GUILD_ID

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(TournamentStart)
    bot.application_command(Hardcore)


class TournamentStart(
    discord.SlashCommand, guilds=[GUILD_ID], name="start", parent=TournamentParent
):

    """Create and start a new tournament."""

    record: Optional[str] = discord.Option(
        description="Your personal record. Format: HH:MM:SS.ss - You can omit the hours or minutes if they are 0."
    )

    async def callback(self) -> None:
        """Callback for submitting records slash command."""
        maps = TournamentCategories(
            ta=TournamentMaps(code="code1", creator="creator", map_name="Hanamura"),
            mc=TournamentMaps(code="code2", creator="creator", map_name="Hanamura"),
            hc=TournamentMaps(code="code3", creator="creator", map_name="Hanamura"),
            bo=TournamentMaps(code="code4", creator="creator", map_name="Hanamura"),
        )
        last_tournament = await Tournament.find_latest()
        if last_tournament:
            last_id = last_tournament.tournament_id
        else:
            last_id = 0

        tournament_document = Tournament(
            tournament_id=last_id + 1,
            name="Tournament Test",
            active=True,
            bracket=False,
            schedule_start=datetime(1, 1, 1),
            schedule_end=datetime(1, 2, 1),
            maps=maps,
            records=TournamentCategories(ta=[], mc=[], hc=[], bo=[]),
            missions=TournamentCategories(
                ta=TournamentMissions(),
                mc=TournamentMissions(),
                hc=TournamentMissions(),
                bo=TournamentMissions(),
            ),
        )

        await tournament_document.insert()
        await self.interaction.response.send_message("BING BONG", ephemeral=True)


class Hardcore(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="hardcore",
    parent=TournamentSubmitParent,
):

    """Hardcore tournament submission."""
