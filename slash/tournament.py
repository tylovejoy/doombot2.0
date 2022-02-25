import asyncio
import datetime
import operator
import re
from logging import getLogger
from typing import Dict, List, Literal, Optional, Tuple, Union

import dateparser
import discord
from discord.utils import MISSING, format_dt

from database.documents import ExperiencePoints
from database.records import Record
from database.tournament import (
    Announcement,
    ShortRecordData,
    Tournament,
    TournamentData,
    TournamentMaps,
    TournamentMissions,
    TournamentRecords,
)
from slash.parents import (
    TournamentMissionsParent,
    TournamentOrgParent,
    TournamentParent,
)
from utils.constants import (
    BOT_ID,
    GUILD_ID,
    HALL_OF_FAME_ID,
    TOURNAMENT_INFO_ID,
    TOURNAMENT_ORG_ID,
    TOURNAMENT_SUBMISSION_ID,
)
from utils.embed import (
    create_embed,
    hall_of_fame,
    records_tournament_embed_fields,
    split_embeds,
)
from utils.enums import Emoji
from utils.errors import InvalidTime
from utils.excel_exporter import init_workbook
from utils.utilities import (
    check_permissions,
    display_record,
    format_missions,
    get_mention,
    logging_util,
    make_ordinal,
    preprocess_map_code,
    time_convert,
    tournament_category_map,
    tournament_category_map_reverse,
)
from views.basic import ConfirmView
from views.paginator import Paginator
from views.tournament import (
    TournamentAnnouncementModal,
    TournamentCategoryView,
    TournamentStartView,
)

logger = getLogger(__name__)


map_data_regex = re.compile(r"(.+)\s-\s(.+)\s-\s(.+)")


def setup(bot):
    logger.info(logging_util("Loading", "TOURNAMENT"))
    bot.application_command(TimeAttackSubmission)
    bot.application_command(MildcoreSubmission)
    bot.application_command(HardcoreSubmission)
    bot.application_command(BonusSubmission)


class TournamentStart(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="start",
    parent=TournamentOrgParent,
):
    """Create and start a new tournament."""

    schedule_start: str = discord.Option(
        description="When should the tournament start?",
    )
    schedule_end: str = discord.Option(
        description="When should the tournament end?",
    )

    async def callback(self) -> None:
        """Callback for submitting records slash command."""
        await self.defer(ephemeral=True)
        if not await check_permissions(self.interaction):
            return

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

        tournament_document = Tournament(
            tournament_id=last_id + 1,
            name="Doomfist Parkour Tournament",
            active=True,
            bracket=False,
            schedule_start=self.schedule_start,
            schedule_end=self.schedule_end,
        )

        view = TournamentStartView(self.interaction)
        await self.interaction.edit_original_message(
            content="Click on the buttons to add necessary info.", view=view
        )
        await view.wait()

        if view.ta_modal:
            setattr(
                tournament_document,
                "ta",
                TournamentData(
                    map_data=TournamentMaps(
                        code=preprocess_map_code(view.ta_modal.code),
                        level=view.ta_modal.level.upper(),
                        creator=view.ta_modal.creator,
                    )
                ),
            )

        if view.mc_modal:
            setattr(
                tournament_document,
                "mc",
                TournamentData(
                    map_data=TournamentMaps(
                        code=preprocess_map_code(view.mc_modal.code),
                        level=view.mc_modal.level.upper(),
                        creator=view.mc_modal.creator,
                    )
                ),
            )
        if view.hc_modal:
            setattr(
                tournament_document,
                "hc",
                TournamentData(
                    map_data=TournamentMaps(
                        code=preprocess_map_code(view.hc_modal.code),
                        level=view.hc_modal.level.upper(),
                        creator=view.hc_modal.creator,
                    )
                ),
            )
        if view.bo_modal:
            setattr(
                tournament_document,
                "bo",
                TournamentData(
                    map_data=TournamentMaps(
                        code=preprocess_map_code(view.bo_modal.code),
                        level=view.bo_modal.level.upper(),
                        creator=view.bo_modal.creator,
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
        await self.interaction.guild.get_channel(TOURNAMENT_ORG_ID).send(
            "Tournament Scheduled...", embed=embed
        )


class ChangeRank(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="changerank",
    parent=TournamentOrgParent,
):
    """Change a users rank in a particular category."""

    user: discord.Member = discord.Option(
        description="Which user do you want to alter?"
    )

    timeattack: Optional[Literal["Gold", "Diamond", "Grandmaster"]] = discord.Option(
        description="Which rank?"
    )
    mildcore: Optional[Literal["Gold", "Diamond", "Grandmaster"]] = discord.Option(
        description="Which rank?"
    )
    hardcore: Optional[Literal["Gold", "Diamond", "Grandmaster"]] = discord.Option(
        description="Which rank?"
    )
    # bonus: Optional[Literal["Gold", "Diamond", "Grandmaster"]] = discord.Option(
    #     description="Which rank?"
    # )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        if not await check_permissions(self.interaction):
            return

        user = await ExperiencePoints.find_user(self.user.id)

        message_content = f"Changing rank(s) for {user.alias}\n"

        if self.timeattack is not MISSING:
            user.rank.ta = self.timeattack
            message_content += f"**Time Attack** rank to **{self.timeattack}**.\n"
        if self.mildcore is not MISSING:
            user.rank.mc = self.mildcore
            message_content += f"**Mildcore** rank to **{self.mildcore}**.\n"
        if self.hardcore is not MISSING:
            user.rank.hc = self.hardcore
            message_content += f"**Hardcore** rank to **{self.hardcore}**.\n"
        # if self.bonus is not MISSING:
        #     user.rank.bo = self.bonus
        #     message_content += f"**Bonus** rank to **{self.bonus}**.\n"

        message_content += "Is this correct?"

        view = ConfirmView()
        if await view.start(self.interaction, message_content, "Confirmed."):
            await user.save()


class ViewTournamentRecords(
    discord.SlashCommand, name="leaderboard", parent=TournamentParent
):
    """View leaderboard for a particular tournament category and optionally tournament rank."""

    category: Literal["Time Attack", "Mildcore", "Hardcore", "Bonus"] = discord.Option(
        description="Which tournament category?",
    )
    rank: Optional[
        Literal["Unranked", "Gold", "Diamond", "Grandmaster"]
    ] = discord.Option(
        description="Which rank to display?",
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        self.category = tournament_category_map_reverse(self.category)

        records = await Tournament.get_records(self.category, rank=self.rank)
        if not records:
            await self.interaction.edit_original_message(content="No records found.")
            return

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
        view = Paginator(embeds, self.interaction.user)
        await view.start(self.interaction)


class TimeAttackSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="ta",
    # parent=SubmitParent,
):
    """Time Attack tournament submission."""

    screenshot: discord.Attachment = discord.Option(
        description="Screenshot of your record."
    )
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(
            self.interaction, self.screenshot, self.record, "ta"
        )


class MildcoreSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="mc",
    # parent=SubmitParent,
):
    """Mildcore tournament submission."""

    screenshot: discord.Attachment = discord.Option(
        description="Screenshot of your record."
    )
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(
            self.interaction, self.screenshot, self.record, "mc"
        )


class HardcoreSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="hc",
    # parent=SubmitParent,
):
    """Hardcore tournament submission."""

    screenshot: discord.Attachment = discord.Option(
        description="Screenshot of your record."
    )
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(
            self.interaction, self.screenshot, self.record, "hc"
        )


class BonusSubmission(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="bo",
    # parent=SubmitParent,
):
    """Bonus tournament submission."""

    screenshot: discord.Attachment = discord.Option(
        description="Screenshot of your record."
    )
    record: str = discord.Option(
        description="What is the record you'd like to submit? HH:MM:SS.ss format. "
    )

    async def callback(self) -> None:
        await tournament_submissions(
            self.interaction, self.screenshot, self.record, "bo"
        )


class TournamentAnnouncement(
    discord.SlashCommand,
    guilds=[GUILD_ID],
    name="announcement",
    parent=TournamentOrgParent,
):
    """Send annoucement."""

    # title: str = discord.Option(description="Title of the announcement.")
    # content: str = discord.Option(
    #     description="Contents of the announcement.",
    # )
    scheduled_start: Optional[str] = discord.Option(
        description="Optional annoucement schedule start time.",
    )

    async def callback(self) -> None:
        if not await check_permissions(self.interaction):
            return
        modal = TournamentAnnouncementModal()

        await self.interaction.response.send_modal(modal)

        timeout_count = 0
        while not modal.done:
            timeout_count += 1
            await asyncio.sleep(1)
            if timeout_count == 600:
                return

        embed = create_embed(title="Announcement", desc="", user=self.interaction.user)
        embed.add_field(name=modal.title_, value=modal.content, inline=False)

        if self.scheduled_start:
            self.scheduled_start = dateparser.parse(
                self.scheduled_start, settings={"PREFER_DATES_FROM": "future"}
            )
            embed.add_field(
                name="Scheduled:",
                value=f"{format_dt(self.scheduled_start, style='R')} - {format_dt(self.scheduled_start, style='F')}",
                inline=False,
            )

        view = TournamentCategoryView(modal.interaction)
        await modal.interaction.edit_original_message(
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

            await modal.interaction.edit_original_message(
                content="Scheduled.", embed=embed, view=view
            )
            embed.remove_field(-1)

            document = Announcement(
                embed=embed.to_dict(), schedule=self.scheduled_start, mentions=mentions
            )
            await document.insert()

            return

        await modal.interaction.edit_original_message(content="Done.", view=view)
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
        await self.defer(ephemeral=True)
        if not await check_permissions(self.interaction):
            return

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
            if self.type == "sub":
                self.target = time_convert(self.target)
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
        if await view.start(
            self.interaction,
            "Is this correct?",
            "Added.",
            embed=embed,
        ):
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
        await self.defer(ephemeral=True)
        if not await check_permissions(self.interaction):
            return

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
    interaction: discord.Interaction,
    screenshot: discord.Attachment,
    record: str,
    category: str,
):
    """Tournament submissions."""
    await interaction.response.defer(ephemeral=True)
    tournament = await Tournament.find_active()
    if not tournament:
        await interaction.edit_original_message(content="Tournament not active!")
        return

    category_attr = getattr(tournament, category)
    if not category_attr:
        await interaction.edit_original_message(content="This category is not active.")
        return

    try:
        record_seconds = time_convert(record)
    except InvalidTime as e:
        await interaction.edit_original_message(content=e)
        return

    already_posted = False
    submission = None
    for r in category_attr.records:
        if r.user_id == interaction.user.id:
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
            record=record_seconds,
            user_id=interaction.user.id,
            attachment_url=screenshot.url,
        )
        category_attr.records.append(submission)

    embed = create_embed(
        f"{tournament_category_map(category)} Submission",
        f"> **Record:** {display_record(submission.record)}",
        interaction.user,
    )
    embed.set_image(url=screenshot.url)

    view = ConfirmView()
    if await view.start(
        interaction,
        "Is this correct?",
        "Submitted.",
        embed=embed,
    ):
        await tournament.save()

        await interaction.guild.get_channel(TOURNAMENT_SUBMISSION_ID).send(embed=embed)

        user = await ExperiencePoints.find_user(interaction.user.id)
        if category == "bo":
            return
        if await user.check_if_unranked(category):
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
        user.xp += round(data["xp"])

        for key in user.xp_avg:
            user.xp_avg[key].pop(0)
            user.xp_avg[key].append(round(data[key]))

            # Find current average for ending summary
            usable_user_xps = [xp for xp in user.xp_avg[key] if xp != 0]
            xp_store[user_id][f"{key}_cur_avg"] = sum(usable_user_xps) / (
                len(usable_user_xps) or 1
            )

        await user.save()

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
    await send_records_to_db(tournament)


async def send_records_to_db(tournament: Tournament):
    """Send tournament records to the standard personal records database collection."""
    for category in ["ta", "mc", "hc", "bo"]:
        data: TournamentData = getattr(tournament, category, None)
        if not data:
            continue
        code = data.map_data.code
        level = data.map_data.level

        for record in data.records:
            search = await Record.filter_search_single(
                map_code=code, map_level=level, user_id=record.user_id
            )
            if not search:
                search = Record(
                    user_id=record.user_id,
                    code=code,
                    level=level,
                    record=record.record,
                    verified=True,
                    attachment_url=record.attachment_url,
                )
            else:
                if search.record <= record.record:
                    continue
                else:
                    search.record = record.record
                    search.attachment_url = record.attachment_url
                    search.verified = True
            await search.save()


async def export_records(tournament: Tournament, thread: discord.Thread):
    await thread.send(
        file=discord.File(
            fp=r"DPK_Tournament.xlsx",
            filename=f"XP_Spreadsheet.xlsx",
        )
    )
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
            embed = create_embed("Submission", "", "")
            embed.add_field(
                name=record.user_data.alias, value=display_record(t_cat.records.record)
            )
            embed.set_image(url=t_cat.records.attachment_url)
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


async def create_hall_of_fame(tournament: Tournament) -> discord.Embed:
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
            user = await ExperiencePoints.find_user(record.user_id)
            top_three_list += (
                f"`{make_ordinal(pos)}` - {user.alias} - {display_record(record.record, tournament=True)} "
                f"{Emoji.display_rank(getattr(user.rank, category))}\n"
            )
        embed.add_field(
            name=tournament_category_map(category)
            + f" ({map_data.code} - {map_data.level})",
            value=top_three_list or "No times submitted! <:CHUMPY:829934452112752672>",
            inline=False,
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
        user_ranks = (await ExperiencePoints.find_user(record.user_id)).rank
        rank = getattr(user_ranks, category)
        split_ranks[rank].append(record)
    return split_ranks


async def compute_leaderboard_xp(
    tournament: Tournament, store: Dict[int, Dict[str, int]]
) -> Tuple[Dict[int, Dict], Dict[str, Dict[str, List[TournamentRecords]]]]:
    """Compute the XP for each leaderboard (rank/category)."""
    multiplier = {
        "ta": 0.14094,
        "mc": 0.3654,
        "hc": 0.8352,
        "bo": 0.3654,
    }
    all_split_records = {}

    for category in ["ta", "mc", "hc", "bo"]:
        all_records = getattr(tournament, category, None)
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
                        / (multiplier[category] * top_record)
                    ) * 2500

                    if formula < 100:
                        xp = 100
                    else:
                        xp = formula
                store[record.user_id][category] += xp
                store[record.user_id]["xp"] += xp
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
            if not store.get(record.user_id):
                store[record.user_id] = {
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
                    "ta_cur_avg": 0,
                    "mc_cur_avg": 0,
                    "hc_cur_avg": 0,
                    "bo_cur_avg": 0,
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
                if not mission:
                    continue

                type_ = mission.type
                target = mission.target

                if (type_ == "sub" and record.record < float(target)) or (
                    type_ == "complete" and record.record
                ):
                    store[record.user_id][mission_category] += 1
                    store[record.user_id]["xp"] += mission_points[mission_category]
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

            if mission.type == "xp" and data["xp"] > int(mission.target):
                store[user_id]["general"] += 1
                store[user_id]["xp"] += 2000

            if mission.type == "missions":
                split = mission.target.split()
                if len(split) != 2:
                    continue

                target_amt = int(split[0])
                target_difficulty = split[1].lower()

                encompass_missions = {
                    "easy": data["easy"]
                    + data["medium"]
                    + data["hard"]
                    + data["expert"],
                    "medium": data["medium"] + data["hard"] + data["expert"],
                    "hard": data["hard"] + data["expert"],
                    "expert": data["expert"],
                }

                if encompass_missions[target_difficulty] >= target_amt:
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
                            if record.user_id == user_id:
                                temp_store[category] += 1
                                break
                if sum(temp_store.values()) >= int(mission.target):
                    store[user_id]["general"] += 1
                    store[user_id]["xp"] += 2000
    return store
