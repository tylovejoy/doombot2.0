from logging import getLogger
from typing import Optional

import dateparser
import discord
from discord.utils import format_dt

from database.tournament import (
    Announcement,
    Tournament,
)
from slash.parents import TournamentParent
from utils.constants import (
    GUILD_ID,
    TOURNAMENT_INFO_ID,
)
from utils.embed import create_embed
from utils.utilities import get_mention

from views.tournament import TournamentCategoryView, TournamentStartView

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(TournamentStart)
    bot.application_command(Hardcore)
    bot.application_command(TournamentAnnouncement)


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
    # parent=TournamentSubmitParent,
):
    """Hardcore tournament submission."""

    async def callback(self) -> None:
        view = TournamentStartView(self.interaction)
        embed = create_embed(
            "Tournament Start Wizard",
            "Click on the buttons to add necessary information.",
            self.interaction.user,
        )
        await self.interaction.response.send_message(embed=embed, view=view)


class TournamentAnnouncement(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="announcement",
    parent=TournamentParent,
):
    """Send annoucement."""

    title: str = discord.Option(description="Title of the announcement.")
    content: str = discord.Option(
        description="Contents of the announcement.",
    )
    scheduled_start: Optional[str] = discord.Option(
        description="Optional annoucement schedule start time.",
    )

    async def callback(self) -> None:
        view = TournamentCategoryView(self.interaction)
        embed = create_embed(title="Announcement", desc="", user=self.interaction.user)
        embed.add_field(name=self.title, value=self.content, inline=False)

        if self.scheduled_start:
            self.scheduled_start = dateparser.parse(
                self.scheduled_start, settings={"PREFER_DATES_FROM": "future"}
            )
            embed.add_field(
                name="Scheduled:",
                value=f"{format_dt(self.scheduled_start, style='R')} - {format_dt(self.scheduled_start, style='F')}",
                inline=False,
            )

        await self.interaction.response.send_message(
            "Select any mentions and confirm announcement is correct.",
            embed=embed,
            view=view,
            ephemeral=True,
        )

        await view.wait()

        mentions = "".join([get_mention(m, self.interaction) for m in view.mentions])

        if not view.confirm.value:
            return

        if self.scheduled_start:
            embed.remove_field(-1)

            document = Announcement(
                embed=embed.to_dict(), schedule=self.scheduled_start, mentions=mentions
            )
            await document.insert()
            return
        view.clear_items()
        await self.interaction.edit_original_message(
            content="Done.", embed=None, view=view
        )
        await self.interaction.guild.get_channel(TOURNAMENT_INFO_ID).send(
            f"{mentions}", embed=embed
        )
