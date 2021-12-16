from datetime import datetime
from logging import getLogger
from typing import Optional

import discord
from database.tournament import (
    TournamentData,
    TournamentMaps,
    Tournament,
    TournamentMissionsCategories,
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

    async def callback(self) -> None:
        """Callback for submitting records slash command."""
        last_tournament = await Tournament.find_latest()
        if last_tournament:
            last_id = last_tournament.tournament_id
        else:
            last_id = 0

        # tournament_document = Tournament(
        #     tournament_id=last_id + 1,
        #     name="Tournament Test",
        #     active=True,
        #     bracket=False,
        #     schedule_start=datetime(1, 1, 1),
        #     schedule_end=datetime(1, 2, 1),
        #     ta=TournamentData(
        #         map_data=TournamentMaps(
        #             code="code1", creator="creator", map_name="Hanamura", level="bing"
        #         ),
        #         missions=TournamentMissionsCategories(
        #             easy=TournamentMissions(type="sub", target="10"),
        #             medium=TournamentMissions(type="sub", target="15"),
        #             hard=TournamentMissions(type="sub", target="20"),
        #             expert=TournamentMissions(type="sub", target="25"),
        #         ),
        #     ),
        #     mc=TournamentData(
        #         map_data=TournamentMaps(
        #             code="code1", creator="creator", map_name="Hanamura", level="bing"
        #         ),
        #         missions=TournamentMissionsCategories(
        #             easy=TournamentMissions(type="sub", target="11"),
        #             medium=TournamentMissions(type="sub", target="16"),
        #             hard=TournamentMissions(type="sub", target="21"),
        #             expert=TournamentMissions(type="sub", target="26"),
        #         ),
        #     ),
        #     hc=TournamentData(
        #         map_data=TournamentMaps(
        #             code="code1", creator="creator", map_name="Hanamura", level="bing"
        #         ),
        #         missions=TournamentMissionsCategories(
        #             easy=TournamentMissions(type="sub", target="12"),
        #             medium=TournamentMissions(type="sub", target="17"),
        #             hard=TournamentMissions(type="sub", target="22"),
        #             expert=TournamentMissions(type="sub", target="27"),
        #         ),
        #     ),
        #     bo=TournamentData(
        #         map_data=TournamentMaps(
        #             code="code1", creator="creator", map_name="Hanamura", level="bing"
        #         ),
        #         missions=TournamentMissionsCategories(
        #             easy=TournamentMissions(type="sub", target="13"),
        #             medium=TournamentMissions(type="sub", target="18"),
        #             hard=TournamentMissions(type="sub", target="23"),
        #             expert=TournamentMissions(type="sub", target="28"),
        #         ),
        #     ),
        #     general_mission=TournamentMissions(type="ya", target="mama")
        # )

        # await tournament_document.insert()

        x = last_tournament.get_all_missions()

        await self.interaction.response.send_message(f"{x}", ephemeral=True)


class Hardcore(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="hardcore",
    parent=TournamentSubmitParent,
):

    """Hardcore tournament submission."""
