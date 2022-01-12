import datetime
from logging import getLogger
from typing import Dict, Optional, Union

import dateparser
import discord
from discord.app import AutoCompleteResponse
from discord.utils import format_dt

from database.tournament import (
    Announcement,
    DifficultyLiteral,
    Tournament,
    TournamentData,
    TournamentMaps,
    TournamentMissions,
    TournamentMissionsCategories,
)
from slash.parents import TournamentMissionsParent, TournamentParent, TournamentSubmitParent
from utils.constants import (
    GUILD_ID,
    TOURNAMENT_INFO_ID,
)
from utils.embed import create_embed
from utils.utilities import check_roles, get_mention, no_perms_warning, tournament_category_map, tournament_category_map_reverse

from views.tournament import TournamentCategoryView, TournamentStartView

logger = getLogger(__name__)


def setup(bot):
    logger.info("Loading Tournament commands...")
    bot.application_command(Test)


class Test(discord.SlashCommand, guilds=[GUILD_ID], name="test"):
    option: bool = discord.Option()

    async def callback(self) -> None:
        print(TournamentParent._children_)
        for x in TournamentParent._children_:
            print(type(x))


class TournamentStart(
    discord.SlashCommand, guilds=[GUILD_ID], name="start", parent=TournamentParent
):
    """Create and start a new tournament."""

    schedule_start: str = discord.Option(
        description="When should the tournament start?",
    )
    schedule_end: str = discord.Option(
        description="When should the tournament end?",
    )
    time_attack: Optional[str] = discord.Option(
        description="CODE - LEVEL NAME - CREATOR",
    )
    mildcore: Optional[str] = discord.Option(
        description="CODE - LEVEL NAME - CREATOR",
    )
    hardcore: Optional[str] = discord.Option(
        description="CODE - LEVEL NAME - CREATOR",
    )
    bonus: Optional[str] = discord.Option(
        description="CODE - LEVEL NAME - CREATOR",
    )

    async def callback(self) -> None:
        """Callback for submitting records slash command."""
        if not check_roles(self.interaction):
            await no_perms_warning(self.interaction)
            return
        await self.interaction.response.defer(ephemeral=True)
        # TODO: Check for active tournaments

        last_tournament = await Tournament.find_latest()
        if last_tournament:
            last_id = last_tournament.tournament_id
        else:
            last_id = 0

        self.schedule_start = dateparser.parse(
            self.schedule_start, settings={"PREFER_DATES_FROM": "future"}
        )
        self.schedule_end = (
            dateparser.parse(
                self.schedule_end, settings={"PREFER_DATES_FROM": "future"}
            )
            - datetime.datetime.now()
            + self.schedule_start
        )
        print(type(self.schedule_end))

        tournament_document = Tournament(
            tournament_id=last_id + 1,
            name="Doomfist Parkour Tournament",
            active=True,
            bracket=False,
            mentions="kdjfgkjdsfg",
            schedule_start=self.schedule_start,
            schedule_end=self.schedule_end,
            ta=TournamentData(
                map_data=TournamentMaps(
                    code="ASSE9", creator="Sven", level="LEVEL 1"
                ),
                missions=TournamentMissionsCategories(),
            ),
            mc=TournamentData(
                map_data=TournamentMaps(
                    code="29Y0P", creator="Sky", level="LEVEL 6"
                ),
                missions=TournamentMissionsCategories(),
            ),
            hc=TournamentData(
                map_data=TournamentMaps(
                    code="5EMMA", creator="Opare", level="LEVEL 9"
                ),
                missions=TournamentMissionsCategories(),
            ),
            # bo=TournamentData(
            #     map_data=TournamentMaps(
            #         code="code1", creator="creator", level="bing"
            #     ),
            #     missions=TournamentMissionsCategories(),
            # ),
        )
        embed = create_embed(
            tournament_document.name, 
            (
                f"Start: {format_dt(self.schedule_start, style='R')} - {format_dt(self.schedule_start, style='F')}\n"
                f"End: {format_dt(self.schedule_end, style='R')} - {format_dt(self.schedule_end, style='F')}\n"
            ),
            self.interaction.user
        )

        for category in ["ta", "mc", "hc", "bo"]:
            data = getattr(getattr(tournament_document, category, None), "map_data", None)
            if getattr(data, "code", None):
                embed.add_field(
                name=f"{tournament_category_map(category)} ({data.code})",
                value=f"***{data.level}*** by {data.creator}",
                inline=False,
            )

        #await tournament_document.insert()
        await self.interaction.edit_original_message(embed=embed)


class Hardcore(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="hardcore",
    parent=TournamentSubmitParent,
):
    """Hardcore tournament submission."""

    async def callback(self) -> None:
        await self.interaction.response.send_message("PONG")


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
        if not check_roles(self.interaction):
            await no_perms_warning(self.interaction)
            return

        await self.interaction.response.defer(ephemeral=True)
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

        view = TournamentCategoryView(self.interaction)
        await self.interaction.edit_original_message(
            content="Select any mentions and confirm announcement is correct.",
            embed=embed,
            view=view,
        )

        await view.wait()

        mentions = "".join([get_mention(tournament_category_map_reverse(m), self.interaction) for m in view.mentions])
        if not view.confirm.value:
            return

        view.clear_items()

        if self.scheduled_start:
            
            await self.interaction.edit_original_message(
                content="Scheduled.", embed=embed, view=view
            )
            embed.remove_field(-1)

            document = Announcement(
                embed=embed.to_dict(), schedule=self.scheduled_start, mentions=mentions
            )
            await document.insert()
            
            return
            
        
        await self.interaction.edit_original_message(
            content="Done.", view=view
        )
        await self.interaction.guild.get_channel(TOURNAMENT_INFO_ID).send(
            f"{mentions}", embed=embed
        )


class TournamentAddMissions(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="add",
    parent=TournamentMissionsParent,
):
    """Add missions."""

    category: str = discord.Option(description="Which tournament category?", autocomplete=True)
    difficulty: str = discord.Option(
        description="Which difficulty?", autocomplete=True
    )
    type: str = discord.Option(description="Which type of mission?", autocomplete=True)
    target: str = discord.Option(
        description="Target value of mission."
    )

    async def callback(self) -> None:
        if not check_roles(self.interaction):
            await no_perms_warning(self.interaction)
            return
        await self.interaction.response.defer(ephemeral=True)
        await self.interaction.edit_original_message(content="Pong")

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        if focused == "category":
            return AutoCompleteResponse({
                "Time Attack": "ta",
                "Mildcore": "mc",
                "Hardcore": "hc",
                "Bonus": "bo",
            })
        if focused == "difficulty":
            return AutoCompleteResponse({
                "Easy": "easy",
                "Medium": "medium",
                "Hard": "hard",
                "Expert": "expert",
                "General": "general",
            })
        if focused == "type":
            diff = options.get("difficulty")
            if diff == "general":
                return AutoCompleteResponse({
                    "XP Threshold": "xp",
                    "Mission Threshold": "missions",
                    "Top Placement": "top",
                })
            if diff != "general":
                return AutoCompleteResponse({
                    "Sub x time": "sub",
                    "Complete entire level": "complete",
                })
