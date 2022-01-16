import datetime
from logging import getLogger

import operator
from typing import Dict, Optional, Tuple, Union, List, Literal

from discord.utils import MISSING, format_dt
import dateparser
import discord
import re

from database.documents import ExperiencePoints
from database.records import Record

from database.tournament import (
    Announcement,
    Tournament,
    TournamentData,
    TournamentMaps,
    TournamentMissions,
    TournamentRecords,
    ShortRecordData,
)
from slash.parents import (
    TournamentMissionsParent,
    TournamentParent,
    SubmitParent,
)
from utils.constants import (
    BOT_ID,
    GUILD_ID,
    TOURNAMENT_INFO_ID,
    TOURNAMENT_SUBMISSION_ID,
    TOURNAMENT_ORG_ID,
    HALL_OF_FAME_ID,
)
from utils.embed import (
    create_embed,
    records_tournament_embed_fields,
    split_embeds,
    hall_of_fame,
)
from utils.excel_exporter import init_workbook
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
    preprocess_map_code,
    make_ordinal,
)
from views.basic import ConfirmView
from views.paginator import Paginator

from views.tournament import TournamentCategoryView

logger = getLogger(__name__)


map_data_regex = re.compile(r"(.+)\s-\s(.+)\s-\s(.+)")


def setup(bot):
    logger.info(logging_util("Loading", "TOURNAMENT"))


class ChangeRank(
    discord.SlashCommand, guilds=[GUILD_ID], name="changerank", parent=TournamentParent
):
    """Change a users rank in a particular category."""

    user: discord.Member = discord.Option(
        description="Which user do you want to alter?"
    )

    category: Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"] = discord.Option(
        description="Which category?"
    )

    rank: Literal["Gold", "Diamond", "Grandmaster"] = discord.Option(
        description="Which rank?"
    )

    async def callback(self) -> None:
        if not check_roles(self.interaction):
            await no_perms_warning(self.interaction)
            return
        await self.interaction.response.defer(ephemeral=True)

        category = tournament_category_map_reverse(self.category)
        user = await ExperiencePoints.find_user(self.user.id)
        ranks = user.rank
        rank = getattr(ranks, category)

        view = ConfirmView()
        await self.interaction.edit_original_message(
            content=(
                f"Changing {user.alias}'s **{self.category}** rank from **{rank}** to **{self.rank}**.\n"
                "Is this correct?"
            ),
            view=view,
        )
        await view.wait()
        if not view.confirm.value:
            return

        setattr(user.rank, category, self.rank)
        await user.save()

        await self.interaction.edit_original_message(
            content=(
                f"Changing {user.alias}'s **{self.category}** rank from **{rank}** to **{self.rank}**.\n"
                "Confirmed."
            ),
            view=view,
        )


class ViewTournamentRecords(
    discord.SlashCommand, guilds=[GUILD_ID], name="leaderboard", parent=TournamentParent
):
    """View leaderboard for a particular tournament category and optionally tournament rank."""

    category: Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"] = discord.Option(
        description="Which tournament category?",
    )
    rank: Literal["Unranked", "Gold", "Diamond", "Grandmaster"] = discord.Option(
        description="Which rank to display?",
    )

    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)
        self.category = tournament_category_map_reverse(self.category)

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

        self.schedule_start: datetime.datetime = dateparser.parse(
            self.schedule_start, settings={"PREFER_DATES_FROM": "future"}
        )
        self.schedule_end: datetime.datetime = (
            dateparser.parse(
                self.schedule_end, settings={"PREFER_DATES_FROM": "future"}
            )
            - datetime.datetime.now()
            + self.schedule_start
        )
        category_abbr = ["ta", "mc", "hc", "bo"]
        category_args = [self.time_attack, self.mildcore, self.hardcore, self.bonus]

        tournament_document = Tournament(
            tournament_id=last_id + 1,
            name="Doomfist Parkour Tournament",
            active=True,
            bracket=False,
            schedule_start=self.schedule_start,
            schedule_end=self.schedule_end,
        )

        for arg, abbr in zip(category_args, category_abbr):
            if arg is MISSING:
                continue
            arg_regex = re.match(map_data_regex, arg)
            code = preprocess_map_code(arg_regex.group(1))
            level_name = arg_regex.group(2).upper()
            setattr(
                tournament_document,
                abbr,
                TournamentData(
                    map_data=TournamentMaps(
                        code=code,
                        level=level_name,
                        creator=arg_regex.group(3),
                    )
                ),
            )

        embed = create_embed(
            tournament_document.name,
            (
                f"Start: {format_dt(self.schedule_start, style='R')} - {format_dt(self.schedule_start, style='F')}\n"
                f"End: {format_dt(self.schedule_end, style='R')} - {format_dt(self.schedule_end, style='F')}\n"
            ),
            self.interaction.user,
        )

        for category in category_abbr:
            data = getattr(
                getattr(tournament_document, category, None), "map_data", None
            )
            if getattr(data, "code", None):
                embed.add_field(
                    name=f"{tournament_category_map(category)}",
                    value=f"Code: {data.code} | {data.level} by {data.creator}",
                    inline=False,
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
        tournament_document.mentions = mentions
        tournament_document.embed = embed.to_dict()
        if not view.confirm.value:
            return

        await tournament_document.insert()
        await self.interaction.edit_original_message(
            content="Tournament scheduled.", view=view
        )


class TimeAttackSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="timeattack",
    parent=SubmitParent,
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
    parent=SubmitParent,
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
    parent=SubmitParent,
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
    parent=SubmitParent,
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
            return discord.AutoCompleteResponse(
                {
                    "Time Attack": "ta",
                    "Mildcore": "mc",
                    "Hardcore": "hc",
                    "Bonus": "bo",
                    "General": "general",
                }
            )
        if focused == "difficulty":
            return discord.AutoCompleteResponse(
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
                return discord.AutoCompleteResponse(
                    {
                        "XP Threshold": "xp",
                        "Mission Threshold": "missions",
                        "Top Placement": "top",
                    }
                )
            if diff != "general":
                return discord.AutoCompleteResponse(
                    {
                        "Sub x time": "sub",
                        "Complete entire level": "complete",
                    }
                )


class TournamentPublishMissions(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="publish",
    parent=TournamentMissionsParent,
):
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
    """Tournament submissions."""
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

    user = await ExperiencePoints.find_user(interaction.user.id)
    if user.check_if_unranked(category):
        await interaction.guild.get_channel(TOURNAMENT_ORG_ID).send(
            f"**ALERT:** {user.alias}/{interaction.user} is Unranked in {tournament_category_map(category)}!\n"
            "Please select their rank before the tournament is over!"
        )


async def end_tournament(client: discord.Client, tournament: Tournament):
    """End of tournament duties.
    Deactivate the tournament, compute leaderboard and mission XP.
    Record XP average for each user.
    Announce the ending of the tournament.
    Send Tournament Orgs a summary.
    """
    tournament.active = False
    tournament.schedule_end = datetime.datetime(year=1, month=1, day=1)
    xp_store = await compute_mission_xp(tournament)

    for user_id, data in xp_store.items():
        user = await ExperiencePoints.find_user(user_id)
        user.xp += data["xp"]
        user.xp_avg.pop(0)
        user.xp_avg.append(data["xp"])
        await user.save()
        # Find current average for ending summary
        usable_user_xps = [xp for xp in user.xp_avg if xp != 0]
        xp_store[user_id]["cur_avg"] = sum(usable_user_xps) / len(usable_user_xps)

    tournament.xp = xp_store
    await init_workbook(tournament)
    await client.get_channel(TOURNAMENT_ORG_ID).send(
        file=discord.File(
            fp=r"DPK_Tournament.xlsx",
            filename=f"DPK_Tournament_{datetime.datetime.today().strftime('%d-%m-%Y')}.xlsx",
        )
    )

    tournament.xp = {str(k): v for k, v in tournament.xp.items()}

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

    # Hall of Fame
    embed = await create_hall_of_fame(tournament)
    hof_msg = await client.get_channel(HALL_OF_FAME_ID).send(embed=embed)
    hof_thread = await hof_msg.create_thread(name="Records Archive")
    # Post export in thread
    await export_records(tournament, hof_thread)
    # TODO: Test and enable
    # await send_records_to_db(tournament)


async def send_records_to_db(tournament: Tournament):
    """Send tournament records to the standard personal records database collection."""
    for category in ["ta", "mc", "hc", "bo"]:
        data: TournamentData = getattr(tournament, category, None)
        if not data:
            continue
        code = data.map_data.code
        level = data.map_data.level

        for record in data.records:
            await Record(
                posted_by=record.posted_by,
                code=code,
                level=level,
                record=record.record,
                verified=True,
                # attachment_url= TODO: attachment
            ).insert()


async def export_records(tournament: Tournament, thread: discord.Thread):
    for category in ["ta", "mc", "hc", "bo"]:
        data: TournamentData = getattr(tournament, category, None)
        await thread.send(
            f"***{10 * '-'} {tournament_category_map(category)} {10 * '-'}***"
        )
        if not data:
            await thread.send(
                f"No times exist for the {tournament_category_map(category)} category!"
            )
            continue

        records = await Tournament.get_records(category)

        embed = create_embed(
            title=f"{tournament_category_map(category)}",
            desc="",
            user="",
        )
        embeds = await split_embeds(
            embed,
            records,
            records_tournament_embed_fields,
            category=category,
        )
        while embeds:
            await thread.send(embeds=embeds[:10])
            embeds = embeds[10:]

        embeds = []
        for record in records:
            t_cat: ShortRecordData = getattr(record, category)
            embed = create_embed("Screenshot Link", "", "")
            embed.add_field(
                name=record.user_data.alias, value=display_record(t_cat.records.record)
            )
            # TODO:
            # embed.set_image(url=t_cat.records.attachment_url)
            embeds.append(embed)

        while embeds:
            await thread.send(embeds=embeds[:10])
            embeds = embeds[10:]


async def start_tournament(client: discord.Client, tournament: Tournament):
    tournament.schedule_start = datetime.datetime(year=1, month=1, day=1)

    await client.get_channel(TOURNAMENT_INFO_ID).send(
        tournament.mentions, embed=discord.Embed.from_dict(tournament.embed)
    )
    await tournament.save()


async def create_hall_of_fame(tournament: Tournament):
    embed = hall_of_fame(tournament.name + " - Top 3", "")
    for category in ["ta", "mc", "hc", "bo"]:
        data: TournamentData = getattr(tournament, category, None)
        if not data:
            continue
        map_data = data.map_data
        records = sorted(data.records, key=operator.attrgetter("record"))

        top_three_list = ""

        for pos, record in enumerate(records, start=1):
            if pos > 3:
                break
            user = await ExperiencePoints.find_user(record.posted_by)
            top_three_list += f"{make_ordinal(pos)} - {user.alias}\n"
        embed.add_field(
            name=tournament_category_map(category) + f" ({map_data.code})",
            value=top_three_list,
        )
    return embed


async def split_leaderboard_ranks(
    records: List[Optional[TournamentRecords]], category: str
) -> Dict[str, List[TournamentRecords]]:
    """Split leaderboard into individual ranks."""

    sorted_records = sorted(records, key=operator.attrgetter("record"))

    split_ranks = {
        "Unranked": [],
        "Gold": [],
        "Diamond": [],
        "Grandmaster": [],
    }
    for record in sorted_records:
        user_ranks = (await ExperiencePoints.find_user(record.posted_by)).rank
        rank = getattr(user_ranks, category)
        split_ranks[rank].append(record)
    return split_ranks


async def compute_leaderboard_xp(
    tournament: Tournament, store: Dict[int, Dict[str, int]]
) -> Tuple[Dict[int, Dict], Dict[str, Dict[str, List[TournamentRecords]]]]:
    """Compute the XP for each leaderboard (rank/category)."""
    multipler = {
        "ta": 0.8352,
        "mc": 0.3654,
        "hc": 0.8352,
        "bo": 0.3654,
    }
    all_split_records = {}

    for category in ["ta", "mc", "hc", "bo"]:
        all_records = getattr(tournament, category, [])
        if not all_records:
            continue
        all_records = all_records.records

        split_sorted_records = await split_leaderboard_ranks(all_records, category)
        all_split_records[category] = split_sorted_records

        for _, records in split_sorted_records.items():
            if not records:
                continue
            top_record = records[0].record

            for record in records:
                # Leaderboard XP
                xp = 0
                if record:
                    formula = (
                        1
                        - (record.record - top_record)
                        / (multipler[category] * top_record)
                    ) * 2500

                    if formula < 100:
                        xp = 100
                    else:
                        xp = formula
                store[record.posted_by][category] += xp
                store[record.posted_by]["xp"] += xp
    return store, all_split_records


async def init_xp_store(tournament: Tournament) -> Dict[int, Dict[str, int]]:
    """Initialize the XP dictionary. Fill with all active players."""
    store = {}
    for category in ["ta", "mc", "hc", "bo"]:
        category_attr: TournamentData = getattr(tournament, category, None)
        if not category_attr:
            continue

        records = category_attr.records

        for record in records:
            if not store.get(record.posted_by):
                store[record.posted_by] = {
                    "easy": 0,
                    "medium": 0,
                    "hard": 0,
                    "expert": 0,
                    "general": 0,
                    "ta": 0,
                    "mc": 0,
                    "hc": 0,
                    "bo": 0,
                    "xp": 0,
                    "cur_avg": 0,
                }
    return store


async def compute_mission_xp(tournament: Tournament) -> Dict[int, Dict]:
    """Compute the XP from difficulty based missions."""
    store, all_records = await compute_leaderboard_xp(
        tournament, await init_xp_store(tournament)
    )

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

    return await compute_general_missions(tournament, store, all_records)


async def compute_general_missions(
    tournament: Tournament,
    store: Dict[int, Dict],
    all_records: Dict[str, Dict[str, List[TournamentRecords]]],
) -> Dict[int, Dict]:
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
                    record_category = all_records.get(category, None)
                    if not record_category:
                        continue
                    for _, rank_records in record_category.items():
                        if not rank_records:
                            continue
                        for i, record in enumerate(rank_records):
                            if i > 2:
                                break
                            if record.posted_by == user_id:
                                temp_store[category] += 1
                                break
                if sum(temp_store.values()) >= mission.target:
                    store[user_id]["general"] += 1
                    store[user_id]["xp"] += 2000
    return store
