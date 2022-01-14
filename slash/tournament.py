import datetime
from logging import getLogger
from typing import Dict, Optional, Union
from discord.partial_emoji import PartialEmoji
from discord.utils import MISSING
import dateparser
import discord
from discord.app import AutoCompleteResponse
from discord.utils import format_dt
from database.documents import ExperiencePoints

from database.tournament import (
    Announcement,
    DifficultyLiteral,
    Tournament,
    TournamentData,
    TournamentMaps,
    TournamentMissions,
    TournamentMissionsCategories,
    TournamentRecords,
)
from slash.parents import (
    TournamentMissionsParent,
    TournamentParent,
    TournamentSubmitParent,
)
from utils.constants import (
    BOT_ID,
    GUILD_ID,
    TOURNAMENT_INFO_ID,
    TOURNAMENT_SUBMISSION_ID,
)
from utils.embed import create_embed, records_tournament_embed_fields, split_embeds
from utils.utilities import (
    check_roles,
    display_record,
    format_missions,
    get_mention,
    logging_util,
    no_perms_warning,
    time_convert,
    tournament_category_map,
    tournament_category_map_reverse,
)
from views.basic import ConfirmView
from views.paginator import Paginator

from views.tournament import TournamentCategoryView, TournamentStartView

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "TOURNAMENT"))
    bot.application_command(Test)


class ViewTournamentRecords(
    discord.SlashCommand, guilds=[GUILD_ID], name="leaderboard", parent=TournamentParent
):
    """View leaderboard for a particular tournament category and optionally tournament rank."""

    category: str = discord.Option(
        description="Which tournament category?",
        autocomplete=True,
    )
    rank: Optional[str] = discord.Option(
        description="Which rank to display?",
        autocomplete=True,
    )

    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)
        if self.category not in ["ta", "mc", "hc", "bo"] or self.rank not in [
            "Unranked",
            "Gold",
            "Diamond",
            "Grandmaster",
            MISSING,
        ]:
            await self.interaction.edit_original_message(content="Invalid arguments.")
            return

        records = await Tournament.get_records(self.category, rank=self.rank)

        if self.rank is MISSING:
            rank_str = "- Overall"
        else:
            rank_str = "- " + self.rank

        embed = create_embed(
            title=f"{tournament_category_map(self.category)} {rank_str}",
            desc="",
            user=self.interaction.user,
        )
        embeds = await split_embeds(
            embed,
            records,
            records_tournament_embed_fields,
            category=self.category,
            rank=self.rank,
        )
        view = Paginator(embeds, self.interaction.user, timeout=None)
        if not view.formatted_pages:
            await self.interaction.edit_original_message(content="No records found.")
            return

        await self.interaction.edit_original_message(
            embed=view.formatted_pages[0], view=view
        )
        await view.wait()

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        if focused == "category":
            return AutoCompleteResponse(
                {
                    "Time Attack": "ta",
                    "Mildcore": "mc",
                    "Hardcore": "hc",
                    "Bonus": "bo",
                }
            )
        if focused == "rank":
            return AutoCompleteResponse(
                {k: k for k in ["Unranked", "Gold", "Diamond", "Grandmaster"]}
            )


class Test(discord.SlashCommand, guilds=[GUILD_ID], name="test"):
    category: str = discord.Option()
    rank: str = discord.Option()

    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)
        records = await Tournament.get_records(self.category, self.rank)
        for x in records:
            print(x)
        await self.interaction.edit_original_message(content="Done.")


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

        if await Tournament.find_active():
            await self.interaction.edit_original_message(
                content="Tournament already active!"
            )
            return

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

        tournament_document = Tournament(
            tournament_id=last_id + 1,
            name="Doomfist Parkour Tournament",
            active=True,
            bracket=False,
            schedule_start=self.schedule_start,
            schedule_end=self.schedule_end,
            ta=TournamentData(
                map_data=TournamentMaps(code="ASSE9", creator="Sven", level="LEVEL 1"),
                missions=TournamentMissionsCategories(),
            ),
            mc=TournamentData(
                map_data=TournamentMaps(code="29Y0P", creator="Sky", level="LEVEL 6"),
                missions=TournamentMissionsCategories(),
            ),
            hc=TournamentData(
                map_data=TournamentMaps(code="5EMMA", creator="Opare", level="LEVEL 9"),
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
            self.interaction.user,
        )

        for category in ["ta", "mc", "hc", "bo"]:
            data = getattr(
                getattr(tournament_document, category, None), "map_data", None
            )
            if getattr(data, "code", None):
                embed.add_field(
                    name=f"{tournament_category_map(category)} ({data.code})",
                    value=f"***{data.level}*** by {data.creator}",
                    inline=False,
                )
        view = TournamentCategoryView(self.interaction)
        await self.interaction.edit_original_message(
            content="Select any mentions and confirm data is correct.", embed=embed
        )
        await view.wait()

        mentions = "".join(
            [
                get_mention(tournament_category_map_reverse(m), self.interaction)
                for m in view.mentions
            ]
        )
        tournament_document.mentions = mentions

        if not view.confirm.value:
            return

        await tournament_document.insert()
        await self.interaction.edit_original_message(
            content="Tournament scheduled.",
        )


class TimeAttackSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="timeattack",
    parent=TournamentSubmitParent,
):
    """Time Attack tournament submission."""

    # TODO: Attachment arg
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(self.interaction, self.record, "ta")


class MildcoreSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="mildcore",
    parent=TournamentSubmitParent,
):
    """Mildcore tournament submission."""

    # TODO: Attachment arg
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(self.interaction, self.record, "mc")


class HardcoreSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="hardcore",
    parent=TournamentSubmitParent,
):
    """Hardcore tournament submission."""

    # TODO: Attachment arg
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(self.interaction, self.record, "hc")


class BonusSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="bonus",
    parent=TournamentSubmitParent,
):
    """Bonus tournament submission."""

    # TODO: Attachment arg
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(self.interaction, self.record, "bo")


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

        mentions = "".join(
            [
                get_mention(tournament_category_map_reverse(m), self.interaction)
                for m in view.mentions
            ]
        )
        if not view.confirm.value:
            return

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

        await self.interaction.edit_original_message(content="Done.", view=view)
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

    category: str = discord.Option(
        description="Which tournament category?", autocomplete=True
    )
    difficulty: str = discord.Option(description="Which difficulty?", autocomplete=True)
    type: str = discord.Option(description="Which type of mission?", autocomplete=True)
    target: str = discord.Option(description="Target value of mission.")

    async def callback(self) -> None:
        if not check_roles(self.interaction):
            await no_perms_warning(self.interaction)
            return
        await self.interaction.response.defer(ephemeral=True)

        tournament = await Tournament.find_active()
        if not tournament:
            await self.interaction.edit_original_message(
                content="No active tournament."
            )
            return

        category = getattr(tournament, self.category)
        if self.category == "general":
            general = TournamentMissions(type=self.type, target=self.target)
            category.append(general)
        else:
            category = category.missions
            difficulty = getattr(category, self.difficulty)
            difficulty.type = self.type
            difficulty.target = self.target

        embed = create_embed(
            "Add missions",
            (
                f"**{tournament_category_map(self.category)}/{self.difficulty.capitalize()}**\n"
                f"{format_missions(self.type, self.target)}"
            ),
            self.interaction.user,
        )
        view = ConfirmView()
        await self.interaction.edit_original_message(
            content="Is this correct?",
            embed=embed,
            view=view,
        )
        await view.wait()

        if not view.confirm.value:
            return

        await self.interaction.edit_original_message(
            content="Added.",
            embed=embed,
            view=view,
        )
        await tournament.save()

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        if focused == "category":
            return AutoCompleteResponse(
                {
                    "Time Attack": "ta",
                    "Mildcore": "mc",
                    "Hardcore": "hc",
                    "Bonus": "bo",
                    "General": "general",
                }
            )
        if focused == "difficulty":
            return AutoCompleteResponse(
                {
                    "Easy": "easy",
                    "Medium": "medium",
                    "Hard": "hard",
                    "Expert": "expert",
                    "General": "general",
                }
            )
        if focused == "type":
            diff = options.get("difficulty")
            if diff == "general":
                return AutoCompleteResponse(
                    {
                        "XP Threshold": "xp",
                        "Mission Threshold": "missions",
                        "Top Placement": "top",
                    }
                )
            if diff != "general":
                return AutoCompleteResponse(
                    {
                        "Sub x time": "sub",
                        "Complete entire level": "complete",
                    }
                )


class TournamentViewMissions(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="publish",
    parent=TournamentMissionsParent,
):
    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)

        tournament = await Tournament.find_active()
        if not tournament:
            await self.interaction.edit_original_message(
                content="No active tournament."
            )
            return

        embed = create_embed(
            "Missions",
            tournament.get_all_missions(),
            self.interaction.user,
        )

        view = TournamentCategoryView(self.interaction)
        await self.interaction.edit_original_message(
            content="Select any mentions and confirm data is correct.",
            embed=embed,
            view=view,
        )
        await view.wait()

        mentions = "".join(
            [
                get_mention(tournament_category_map_reverse(m), self.interaction)
                for m in view.mentions
            ]
        )

        if not view.confirm.value:
            return

        await self.interaction.edit_original_message(content="Done.", view=view)
        await self.interaction.guild.get_channel(TOURNAMENT_INFO_ID).send(
            f"{mentions}", embed=embed
        )


async def tournament_submissions(
    interaction: discord.Interaction, record: str, category: str
):
    await interaction.response.defer(ephemeral=True)
    tournament = await Tournament.find_active()
    if not tournament:
        await interaction.edit_original_message(content="Tournament not active!")
        return

    category_attr = getattr(tournament, category)
    record_seconds = time_convert(record)

    already_posted = False
    submission = None
    for r in category_attr.records:
        if r.posted_by == interaction.user.id:
            if record_seconds >= r.record:
                await interaction.edit_original_message(
                    content="Record must be faster than previously submitted record."
                )
                return
            already_posted = True
            r.record = record_seconds
            submission = r
            break

    if not already_posted:
        submission = TournamentRecords(
            record=record_seconds, posted_by=interaction.user.id, attachment_url=""
        )
        category_attr.records.append(submission)

    view = ConfirmView()

    embed = create_embed(
        f"{tournament_category_map(category)} Submission",
        f"> **Record:** {display_record(submission.record)}",
        interaction.user,
    )
    await interaction.edit_original_message(
        content="Is this correct?", embed=embed, view=view
    )

    await view.wait()
    if not view.confirm.value:
        return

    await interaction.edit_original_message(
        content="Submitted.", embed=embed, view=view
    )
    await tournament.save()

    await interaction.guild.get_channel(TOURNAMENT_SUBMISSION_ID).send(embed=embed)


async def end_tournament(client: discord.Client, tournament: Tournament):
    tournament.active = False
    tournament.schedule_end = datetime.datetime(year=1, month=1, day=1)
    xp_store = compute_mission_xp(tournament)

    for user_id, data in xp_store.items():
        user = await ExperiencePoints.find_user(user_id)
        user.xp += data["xp"]
        user.xp_avg.pop(0)
        user.xp_avg.append(data["xp"])
        await user.save()
        # Find current average for ending summary
        xp_store[user_id]["cur_avg"] = sum([xp for xp in user.xp_avg if xp != 0])

    await tournament.save()
    embed = create_embed(
        "Tournament Announcement",
        "",
        client.get_user(BOT_ID),
    )
    embed.add_field(
        name="The round has ended!",
        value="Stay tuned for the next announcement!",
    )
    await client.get_channel(TOURNAMENT_INFO_ID).send(tournament.mentions, embed=embed)

    # TODO: Send summary to #org


async def start_tournament(tournament: Tournament):
    pass


def compute_mission_xp(tournament: Tournament) -> dict:
    # TODO: Leaderboard XP computation

    store = {}
    mission_points = {
        "expert": 2000,
        "hard": 1500,
        "medium": 1000,
        "easy": 500,
    }
    for category in ["ta", "mc", "hc", "bo"]:
        category_attr: TournamentData = getattr(tournament, category, None)
        if not category_attr:
            continue

        records = category_attr.records
        missions = category_attr.missions

        for record in records:
            if not store.get(record.posted_by):
                store[record.posted_by] = {
                    "easy": 0,
                    "medium": 0,
                    "hard": 0,
                    "expert": 0,
                    "general": 0,
                    "xp": 0,
                    "cur_avg": 0,
                }
            # Goes hardest to easiest, because highest mission only
            for mission_category in ["expert", "hard", "medium", "easy"]:
                mission: TournamentMissions = getattr(missions, mission_category, None)
                if not mission or mission.type or mission.target:
                    continue

                type_ = mission.type
                target = mission.target

                if (type_ == "sub" and record.record < float(target)) or (
                    type_ == "complete" and record.record
                ):
                    store[record.posted_by][mission_category] += 1
                    store[record.posted_by]["xp"] += mission_points[mission_category]
                    break
    return compute_general_missions(tournament, store)


def compute_general_missions(tournament: Tournament, store: dict) -> dict:
    general_missions = tournament.general

    for user_id, data in store.items():
        for mission in general_missions:
            total_missions = (
                data["easy"] + data["medium"] + data["hard"] + data["expert"]
            )
            if (mission.type == "xp" and data["xp"] > mission.target) or (
                mission.type == "missions" and total_missions >= mission.target
            ):
                store[user_id]["general"] += 1
                store[user_id]["xp"] += 2000

            if mission.type == "top":
                temp_store = {
                    "ta": 0,
                    "mc": 0,
                    "hc": 0,
                    "bo": 0,
                }
                for category in ["ta", "mc", "hc", "bo"]:
                    category_attr: TournamentData = getattr(tournament, category, None)
                    if not category_attr:
                        continue

                    records = category_attr.records
                    for i, record in enumerate(records):
                        if i > 2:
                            break
                        if record.posted_by == user_id:
                            temp_store[category] += 1
                            break
                if sum(temp_store.values()) >= mission.target:
                    store[user_id]["general"] += 1
                    store[user_id]["xp"] += 2000
    return store
