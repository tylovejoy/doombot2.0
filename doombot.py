from logging import getLogger
from os import name
import aiohttp

import discord
from discord.ext import commands

from database.documents import EXPRanks, ExperiencePoints, Starboard, database_init
from database.records import Record
from utils.constants import (
    BOT_ID,
    NON_SPR_RECORDS_ID,
    SPR_RECORDS_ID,
    SUGGESTIONS_ID,
    TOP_RECORDS_ID,
    TOP_SUGGESTIONS_ID,
)
from utils.utilities import display_record, star_emoji

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
        )
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"),
            case_insensitive=True,
            description="",
            intents=intents,
            slash_command_guilds=[195387617972322306],
        )
        self.suggestion_channel = self.get_channel(SUGGESTIONS_ID)
        self.top_suggestions = self.get_channel(TOP_SUGGESTIONS_ID)

        self.spr_record_channel = self.get_channel(SPR_RECORDS_ID)
        self.other_record_channel = self.get_channel(NON_SPR_RECORDS_ID)

        self.top_records = self.get_channel(TOP_RECORDS_ID)

        self.channel_map = {
            SPR_RECORDS_ID: self.spr_record_channel,
            NON_SPR_RECORDS_ID: self.other_record_channel,
            SUGGESTIONS_ID: self.suggestion_channel,
        }
        self.ws_list = None

    async def on_ready(self):
        """Display bot info on ready event."""
        app_info = await self.application_info()
        logger.info(
            f"{DOOMBOT_ASCII}"
            f"\nLogged in as: {self.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {app_info.owner}\n"
        )
        await database_init()
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

    async def on_member_join(self, member: discord.Member):
        new_user = ExperiencePoints(
            user_id=member.id,
            alias=member.name,
            alerts_enabled=True,
        )
        await new_user.save()
        logger.info(f"Adding new user: {new_user.alias} {new_user.user_id}")

    async def on_message(self, message: discord.Message):
        # Suggestions
        if message.channel.id == SUGGESTIONS_ID:
            await message.add_reaction(emoji="<:upper:787788134620332063>")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == BOT_ID:
            return

        if payload.emoji != discord.PartialEmoji.from_str(
            "<:upper:787788134620332063>"
        ):
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
            self.channel_map[payload.channel_id]
            .get_partial_message(payload.message_id)
            .fetch()
        )

        if entry.starboard_id == 0 and payload.channel_id == SUGGESTIONS_ID:
            embed = discord.Embed(
                description=message.content,
                color=0xF7BD00,
            )
            embed.set_author(
                name=message.author.name, icon_url=message.author.avatar.url
            )
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message: discord.Message = await self.top_suggestions.send(
                f"{star_emoji(entry.stars)} **{entry.stars}**",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.save()
            thread = await starboard_message.start_thread(
                name=message.content[:100], auto_archive_duration=1440
            )
            await thread.add_user(message.author)

        elif entry.starboard_id == 0 and payload.channel_id in [
            NON_SPR_RECORDS_ID,
            SPR_RECORDS_ID,
        ]:
            record = await Record.find_one({"message_id": payload.message_id})
            if record is None:
                return
            embed = discord.Embed(
                description=(
                    f"> **Code:** {record.code}\n"
                    f"> **Level:** {record.level.upper()}\n"
                    f"> **Record:** {display_record(record.record)}\n"
                ),
                color=0xF7BD00,
            )
            user: discord.Member = self.get_user(record.posted_by)

            embed.set_author(name=user.name, icon_url=user.avatar.url)
            embed.add_field(name="Original", value=f"[Jump!]({entry.jump})")
            starboard_message = await self.top_records.send(
                f"{star_emoji(entry.stars)} **{entry.stars}** {message.channel.mention}",
                embed=embed,
            )
            entry.starboard_id = starboard_message.id
            await entry.save()

        else:
            starboard_message = self.channel_map[
                payload.channel_id
            ].get_partial_message(entry.starboard_id)
            await starboard_message.edit(
                content=f"{star_emoji(entry.stars)} **{entry.stars}**"
            )
