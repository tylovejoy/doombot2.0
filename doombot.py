import asyncio
import datetime
from logging import getLogger
import random
from typing import List

import aiohttp
import discord
from discord import RawMessageUpdateEvent
from discord.ext import commands, tasks

from database.documents import (
    ColorRoles,
    Events,
    ExperiencePoints,
    EXPRanks,
    Starboard,
    VerificationViews,
    Voting,
)
from database.records import Record
from database.tournament import Announcement, Duel, Tournament
from slash.mods import VotingView

from slash.tournament import end_tournament, start_tournament

from utils.constants import (
    BOT_ID,
    DUELS_ID,
    GUILD_ID,
    NON_SPR_RECORDS_ID,
    SPR_RECORDS_ID,
    SUGGESTIONS_ID,
    TOP_RECORDS_ID,
    TOP_SUGGESTIONS_ID,
    TOURNAMENT_INFO_ID,
    TOURNAMENT_SUBMISSION_ID,
    EMOJI_SUGG,
)
from utils.enums import Emoji
from utils.utilities import display_record, logging_util, star_emoji
from views.records import VerificationView
from views.roles import ColorRolesView, PronounRoles, ServerRelatedPings, TherapyRole

logger = getLogger(__name__)

DOOMBOT_ASCII = r"""
______  _____  _____ ___  _________  _____  _____
|  _  \|  _  ||  _  ||  \/  || ___ \|  _  ||_   _|
| | | || | | || | | || .  . || |_/ /| | | |  | |
| | | || | | || | | || |\/| || ___ \| | | |  | |
| |/ / \ \_/ /\ \_/ /| |  | || |_/ /\ \_/ /  | |
|___/   \___/  \___/ \_|  |_/\____/  \___/   \_/
"""


class DoomBot(discord.Client):
    def __init__(self, **kwargs):
        """Initialize Bot."""
        intents = discord.Intents(
            guild_reactions=True,
            guild_messages=True,
            guilds=True,
            dm_reactions=True,
            dm_messages=True,
            webhooks=True,
            members=True,
            emojis=True,
            scheduled_events=True,
        )
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"),
            case_insensitive=True,
            description="",
            intents=intents,
            slash_command_guilds=[195387617972322306],
        )
        self.suggestion_channel = None
        self.top_suggestions = None

        self.spr_record_channel = None
        self.other_record_channel = None

        self.top_records = None

        self.channel_map = None
        self.ws_list = None
        self.verification_views_added = False
        self.persistent_views_added = False
        self.guild = None

        self.everyone = None
        self.submissions_channel = None
        self.allow_submissions = None
        self.disallow_submissions = None

        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()
        return await super().close()

    async def on_ready(self):
        """Display bot info on ready event."""
        app_info = await self.application_info()
        logger.info(
            f"{DOOMBOT_ASCII}"
            f"\nLogged in as: {self.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {app_info.owner}\n"
        )
        self.guild = self.get_guild(GUILD_ID)
        self.everyone = self.guild.default_role

        self.suggestion_channel = self.get_channel(SUGGESTIONS_ID)
        self.top_suggestions = self.get_channel(TOP_SUGGESTIONS_ID)

        self.spr_record_channel = self.get_channel(SPR_RECORDS_ID)
        self.other_record_channel = self.get_channel(NON_SPR_RECORDS_ID)

        self.top_records = self.get_channel(TOP_RECORDS_ID)

        self.channel_map = {
            SPR_RECORDS_ID: self.spr_record_channel,
            NON_SPR_RECORDS_ID: self.other_record_channel,
            SUGGESTIONS_ID: self.suggestion_channel,
            TOP_RECORDS_ID: self.top_records,
            TOP_SUGGESTIONS_ID: self.top_suggestions,
        }
        self.channel_map_top = {
            SPR_RECORDS_ID: self.top_records,
            NON_SPR_RECORDS_ID: self.top_records,
            SUGGESTIONS_ID: self.top_suggestions,
        }

        self.submissions_channel = self.guild.get_channel(TOURNAMENT_SUBMISSION_ID)
        self.allow_submissions = self.submissions_channel.overwrites_for(self.everyone)
        self.disallow_submissions = self.submissions_channel.overwrites_for(
            self.everyone
        )
        self.allow_submissions.update(send_messages=True)
        self.disallow_submissions.update(send_messages=False)

        if not self.annoucement_checker.is_running():
            logger.info(logging_util("Task Initialize", "ANNOUNCEMENTS"))
            self.annoucement_checker.start()
        if not self.tournament_checker.is_running():
            logger.info(logging_util("Task Initialize", "TOURNAMENT"))
            self.tournament_checker.start()
        if not self.events_checker.is_running():
            logger.info(logging_util("Task Initialize", "EVENTS"))
            self.events_checker.start()
        if not self.duel_checker.is_running():
            logger.info(logging_util("Task Initialze", "DUELS"))
            self.duel_checker.start()
        if not self.cool_lounge.is_running():
            logger.info(logging_util("Task Initialze", "COOL LOUNGE"))
            self.cool_lounge.start()

        async with aiohttp.ClientSession() as session:

            url = "https://workshop.codes/wiki/dictionary"
            async with session.get(url) as resp:
                self.ws_list = (
                    (await resp.text())
                    .lstrip("[")
                    .rstrip("]")
                    .replace('"', "")
                    .split(",")
                )

        if not self.persistent_views_added:
            colors = await ColorRoles.find().sort("+sort_order").to_list()
            view = ColorRolesView(colors)
            self.add_view(view, message_id=960946616288813066)
            await self.guild.get_channel(752273327749464105).get_partial_message(
                960946616288813066
            ).edit(view=view)

            self.add_view(ServerRelatedPings(), message_id=960946617169612850)
            self.add_view(PronounRoles(), message_id=960946618142699560)
            self.add_view(TherapyRole(), message_id=1005874559037231284)

            self.persistent_views_added = True

        if not self.verification_views_added:
            logger.info(logging_util("Task Initialize", "VERIFICATION VIEWS"))
            views = await VerificationViews.find().to_list()
            for view in views:
                self.add_view(VerificationView(), message_id=view.message_id)
            self.verification_views_added = True

    @tasks.loop(minutes=10)
    async def cool_lounge(self):
        """Rotate members in cool lounge."""
        return
        choices = random.choices(self.guild.members, k=10)
        channel = self.guild.get_channel(976939041712922634)
        for member in channel.overwrites:
            if isinstance(member, discord.Member):
                await channel.set_permissions(
                    member, overwrite=None, reason="Cool Lounge -"
                )

        for member in choices:
            await channel.set_permissions(
                member,
                overwrite=discord.PermissionOverwrite(read_messages=True),
                reason="Cool Lounge +",
            )

    @tasks.loop(seconds=30)
    async def duel_checker(self):
        """Check for duel endings."""
        all_duels: List[Duel] = await Duel.find_all().to_list()
        if not all_duels:
            return

        for duel in all_duels:
            if not duel.end_time:
                return
            if duel.end_time > datetime.datetime.now():
                return

            if not duel.player1.record and not duel.player2.record:
                await self.get_guild(GUILD_ID).get_channel_or_thread(
                    DUELS_ID
                ).get_partial_message(duel.channel_msg).delete()
                await self.get_guild(GUILD_ID).get_channel_or_thread(
                    duel.thread
                ).delete()
                await duel.delete()
                return

            if duel.player1.record is None:
                duel.player1.record = duel.player2.record * 2
            elif duel.player2.record is None:
                duel.player2.record = duel.player1.record * 2

            if duel.player1.record < duel.player2.record:
                await ExperiencePoints.duel_end(
                    winner=duel.player1.user_id,
                    loser=duel.player2.user_id,
                    wager=duel.wager,
                )
                winner = duel.player1.user_id

            else:
                await ExperiencePoints.duel_end(
                    winner=duel.player2.user_id,
                    loser=duel.player1.user_id,
                    wager=duel.wager,
                )
                winner = duel.player2.user_id
            winner = self.get_guild(GUILD_ID).get_member(winner)
            msg = (
                await self.get_guild(GUILD_ID)
                .get_channel(DUELS_ID)
                .fetch_message(duel.channel_msg)
            )
            await msg.edit(content=f"THE WINNER IS {winner.mention}!\n" + msg.content)
            await self.get_channel(duel.thread).archive(locked=True)
            await duel.delete()

    @tasks.loop(seconds=30)
    async def tournament_checker(self):
        """Periodically check for the start/end of tournaments."""
        tournament = await Tournament.find_active()
        if not tournament:
            return

        schedules = [tournament.schedule_start, tournament.schedule_end]
        sentinel = datetime.datetime(year=1, month=1, day=1)

        # Deactivate ended tournament
        if all([s == sentinel for s in schedules]):
            tournament.active = False
            await tournament.save()
            return

        # Check to start tournament
        if datetime.datetime.now() >= tournament.schedule_start != sentinel:
            logger.info(logging_util("Task Start", "STARTING TOURNAMENT"))
            await self.submissions_channel.set_permissions(
                self.everyone,
                overwrite=self.allow_submissions,
                reason="Tournament Started.",
            )
            await start_tournament(self, tournament)
            return

        # Check to end tournament
        if datetime.datetime.now() >= tournament.schedule_end != sentinel:
            logger.info(logging_util("Task Start", "ENDING TOURNAMENT"))
            await self.submissions_channel.set_permissions(
                self.everyone,
                overwrite=self.disallow_submissions,
                reason="Tournament Ended.",
            )
            await end_tournament(self, tournament)
            return

    @tasks.loop(seconds=30)
    async def annoucement_checker(self):
        """Periodically check for scheduled tournament announcements."""
        announcements = await Announcement.find().to_list()
        for announcement in announcements:
            if datetime.datetime.now() >= announcement.schedule:
                embed = discord.Embed.from_dict(announcement.embed)
                info_channel = self.get_channel(TOURNAMENT_INFO_ID)
                await info_channel.send(announcement.mentions, embed=embed)
                await announcement.delete()

    @tasks.loop(seconds=30)
    async def events_checker(self):
        """Periodically check for events."""
        events = await Events.find().to_list()

        for event in events:
            if (
                not event.started
                and event.schedule_start
                > datetime.datetime.now() - datetime.timedelta(minutes=3)
            ):
                category = await self.guild.create_category(
                    "Event", reason="Event Night start", position=0
                )
                text = await category.create_text_channel("Event Chat")
                voice = await category.create_voice_channel("Event Voicechat")
                event.category = category.id
                event.text = text.id
                event.voice = voice.id
                event.started = True
                await event.save()
                await asyncio.sleep(5)
                await self.http.modify_guild_scheduled_event(
                    GUILD_ID,
                    event.event_id,
                    channel_id=voice.id,
                    entity_type=2,
                    entity_metadata=None,
                )
                await self.http.modify_guild_scheduled_event(
                    GUILD_ID,
                    event.event_id,
                    status=2,
                )

    @staticmethod
    async def on_member_join(member: discord.Member):
        search = await ExperiencePoints.find_user(member.id)
        if search:
            return
        new_user = ExperiencePoints(
            user_id=member.id,
            alias=member.name,
            alerts_enabled=True,
            rank=EXPRanks(
                ta="Unranked",
                mc="Unranked",
                hc="Unranked",
                bo="Grandmaster",
            ),
        )
        await new_user.save()
        logger.info(f"Adding new user: {new_user.alias} {new_user.user_id}")

    async def on_guild_scheduled_event_update(self, guild, before, after):
        pass

    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent):
        if payload.channel_id == EMOJI_SUGG:
            await (
                await self.get_channel(EMOJI_SUGG).fetch_message(payload.message_id)
            ).delete()

    @staticmethod
    async def on_message(message: discord.Message):
        # Suggestions
        if message.channel.id == SUGGESTIONS_ID:
            await message.add_reaction(discord.PartialEmoji.from_str(Emoji.upper()))

    @staticmethod
    async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
        if payload.channel_id not in [
            SUGGESTIONS_ID,
            SPR_RECORDS_ID,
            NON_SPR_RECORDS_ID,
        ]:
            return

        search = await Starboard.find_one(Starboard.starboard_id == payload.message_id)
        if search:
            await search.delete()

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == BOT_ID:
            return

        if payload.emoji != discord.PartialEmoji.from_str(Emoji.upper()):
            return
        if payload.channel_id not in [
            SUGGESTIONS_ID,
            NON_SPR_RECORDS_ID,
            SPR_RECORDS_ID,
        ]:
            return

        entry: Starboard = await Starboard.search(payload.message_id)
        if entry is None:  # Create a new entry if not already
            entry = Starboard(
                message_id=payload.message_id,
                jump=f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}",
            )
        elif payload.user_id in entry.reacted:  # Ignore if a user has already reacted.
            return

        entry.stars += 1
        entry.reacted = entry.reacted + [payload.user_id]
        await entry.save()

        if entry.stars < 10 and payload.channel_id == SUGGESTIONS_ID:
            return

        if entry.stars < 5 and payload.channel_id in [
            NON_SPR_RECORDS_ID,
            SPR_RECORDS_ID,
        ]:
            return

        message = (
            await self.channel_map[payload.channel_id]
            .get_partial_message(payload.message_id)
            .fetch()
        )

        if entry.starboard_id != 0:
            starboard_message = self.channel_map_top[
                payload.channel_id
            ].get_partial_message(entry.starboard_id)
            await starboard_message.edit(
                content=f"{star_emoji(entry.stars)} **{entry.stars}** {message.channel.mention}"
            )
            return

        if payload.channel_id == SUGGESTIONS_ID:
            embed = discord.Embed(
                description=message.content,
                color=0xF7BD00,
            )
            embed.set_author(
                name=message.author.name, icon_url=message.author.display_avatar.url
            )
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message = await self.top_suggestions.send(
                f"{star_emoji(entry.stars)} **{entry.stars}**",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.save()
            thread = await starboard_message.create_thread(
                name=message.content[:100], auto_archive_duration=1440
            )
            await thread.add_user(message.author)

        elif payload.channel_id in [
            NON_SPR_RECORDS_ID,
            SPR_RECORDS_ID,
        ]:
            record = await Record.find_one(Record.message_id == payload.message_id)
            if record is None:
                return
            embed = discord.Embed(
                description=(
                    f"> **Code:** {record.code}\n"
                    f"> **Level:** {discord.utils.escape_markdown(record.level)}\n"
                    f"> **Record:** {display_record(record.record)}\n"
                ),
                color=0xF7BD00,
            )
            user = self.get_user(record.user_id)

            embed.set_author(name=user.name, icon_url=user.display_avatar.url)
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message = await self.top_records.send(
                f"{star_emoji(entry.stars)} **{entry.stars}** {message.channel.mention}",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.save()

    @staticmethod
    async def on_thread_update(before: discord.Thread, after: discord.Thread):
        if before.parent_id in [
            856605387050188821,
            840614462494081075,
        ]:  # ignore new maps channel and hall of fame
            return
        if after.archived and not after.locked:
            await after.edit(archived=False)
            logger.info(f"Auto-unarchived thread: {after.id}")
