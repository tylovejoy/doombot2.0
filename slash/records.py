from logging import getLogger
from typing import Optional

import discord
from discord.utils import MISSING

from database.documents import ExperiencePoints, VerificationViews
from database.records import Record
from slash.parents import DeleteParent, SubmitParent
from slash.slash_command import RecordSlash, Slash, UserSlash
from utils.constants import (
    GUILD_ID,
    NON_SPR_RECORDS_ID,
    SPR_RECORDS_ID,
    VERIFICATION_CHANNEL_ID,
)
from utils.embed import (
    create_embed,
    records_basic_embed_fields,
    records_board_embed_fields,
    records_wr_embed_fields,
    split_embeds,
)
from utils.enums import Emoji
from utils.errors import RecordNotFaster, SearchNotFound
from utils.records import delete_hidden, personal_best, world_records
from utils.utilities import (
    check_channels,
    check_permissions,
    find_alt_map_code,
    logging_util,
    make_ordinal,
    preprocess_level_name,
    preprocess_map_code,
    time_convert,
)
from views.basic import ConfirmView
from views.paginator import Paginator
from views.records import RecordSubmitView, VerificationView, find_orig_msg

logger = getLogger(__name__)


def setup(bot: discord.Client):
    logger.info(logging_util("Loading", "RECORDS"))
    bot.application_command(ViewRecords)
    bot.application_command(PersonalRecords)
    bot.application_command(PersonalRecordsShort)
    bot.application_command(PersonalRecordsUserCommand)
    bot.application_command(WorldRecords)
    bot.application_command(WorldRecordsShort)
    bot.application_command(WorldRecordsUserCommand)


async def check_user(user: discord.User):
    """Check if user exists, if not create a new user."""
    user = await ExperiencePoints.find_user(user.id)
    if not user:
        new_user = ExperiencePoints(
            user_id=user.id,
            alias=user.name,
            alerts_enabled=True,
        )
        await new_user.insert()
        return new_user
    return user


class SubmitRecord(RecordSlash, guilds=[GUILD_ID], name="record", parent=SubmitParent):
    """Submit personal records to the database."""

    screenshot: discord.Attachment = discord.Option(
        description="Screenshot of your record."
    )
    map_code: str = discord.Option(
        description="Workshop code for this parkour record.",
        autocomplete=True,
    )
    map_level: str = discord.Option(
        description="Level name for this record. Submit exactly what is shown on the leaderboard.",
        autocomplete=True,
    )
    record: str = discord.Option(
        description="Your personal record. Format: HH:MM:SS.ss - You can omit the hours or minutes if they are 0."
    )

    async def callback(self) -> None:
        """Callback for submitting records slash command."""
        await self.defer(ephemeral=True)

        await check_channels(self.interaction, [SPR_RECORDS_ID, NON_SPR_RECORDS_ID])

        self.map_code = preprocess_map_code(self.map_code)
        self.map_code, code_changed = await find_alt_map_code(self.map_code)

        self.map_level = preprocess_level_name(self.map_level)

        record_seconds = time_convert(self.record)
        await check_user(self.interaction.user)

        record_document = await Record.filter_search_single(
            map_code=self.map_code,
            map_level=self.map_level,
            user_id=self.interaction.user.id,
        )

        # Check if new record is faster than a verified one.
        if (
            record_document
            and record_seconds >= record_document.record
            and record_document.verified
        ):
            raise RecordNotFaster("Personal best needs to be faster to update.")

        # Create initial document if none found.
        if not record_document:
            record_document = Record(
                user_id=self.interaction.user.id,
                code=self.map_code,
                level=self.map_level,
                verified=False,
                message_id=0,
                hidden_id=0,
                record=0.0,
                attachment_url=self.screenshot.url,
            )

        record_document.record = record_seconds
        record_document.attachment_url = self.screenshot.url

        embed = create_embed(
            title="New submission", desc="", user=self.interaction.user
        )
        embed.add_field(**await records_basic_embed_fields(record_document))
        embed.set_image(url=self.screenshot.url)

        view = RecordSubmitView()

        correct_msg = "Is this correct?"
        if code_changed:
            correct_msg += " **MAP CODE CHANGED TO KNOWN ALIAS**"

        await self.interaction.edit_original_message(
            content=correct_msg, view=view, embed=embed
        )
        await view.wait()

        if not view.confirm.value:
            return
        await record_document.save()

        rank = getattr(
            await Record.find_current_rank(
                self.map_code, self.map_level, self.interaction.user.id
            ),
            "rank",
            "None",
        )

        view.clear_items()
        await self.interaction.edit_original_message(
            content="Submitted.",
            view=view,
        )

        # Delete old submission
        try:
            original = await find_orig_msg(self.interaction, record_document)
            await original.delete()
        except (discord.NotFound, discord.HTTPException, AttributeError):
            pass
        # Delete old verification
        try:
            await delete_hidden(self.interaction, record_document)
        except (discord.NotFound, discord.HTTPException, AttributeError):
            pass

        message = await self.interaction.channel.send(
            content=(
                f"{Emoji.TIME} Waiting for verification...\n"
                f"Your record will be {make_ordinal(rank)} on the leaderboard once verified."
            ),
            embed=embed,
        )
        record_document.message_id = message.id

        # Send verification notification.
        verification_channel = self.interaction.guild.get_channel(
            VERIFICATION_CHANNEL_ID
        )
        verify_view = VerificationView()
        hidden_msg = await verification_channel.send(embed=embed, view=verify_view)
        record_document.hidden_id = hidden_msg.id
        await VerificationViews(message_id=hidden_msg.id).save()
        await record_document.save()


class DeleteRecord(RecordSlash, guilds=[GUILD_ID], name="record", parent=DeleteParent):
    """Delete personal records."""

    map_code: str = discord.Option(
        description="Workshop code for this parkour record.",
        autocomplete=True,
    )
    map_level: str = discord.Option(
        description="Level name for this record. Submit exactly what is shown on the leaderboard.",
        autocomplete=True,
    )
    user: Optional[discord.Member] = discord.Option(
        description="User whose record you wish to delete. (MOD ONLY)"
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        self.map_level = preprocess_level_name(self.map_level)

        if self.user != self.interaction.user:
            await check_permissions(self.interaction)
            user_id = self.user.id
        else:
            user_id = self.interaction.user.id

        record_document = await Record.filter_search_single(
            map_code=self.map_code, map_level=self.map_level, user_id=user_id
        )

        embed = create_embed(title="Delete Record", desc="", user=self.interaction.user)
        embed.add_field(**await records_basic_embed_fields(record_document))

        view = RecordSubmitView()
        await self.interaction.edit_original_message(
            content="Do you want to delete this?", view=view, embed=embed
        )
        await view.wait()

        if not view.confirm.value:
            return

        view.clear_items()
        await self.interaction.edit_original_message(content="Deleted.", view=view)
        await delete_hidden(self.interaction, record_document)
        await record_document.delete()


class ViewRecords(RecordSlash, name="leaderboard"):
    """View leaderboard for a particular map code and/or map level."""

    map_code: str = discord.Option(
        description="Workshop code to search for.",
        autocomplete=True,
    )
    map_level: Optional[str] = discord.Option(
        description="Level name to search for. Leave blank if you want to view world records for a specific map code.",
        autocomplete=True,
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        self.map_code, _ = await find_alt_map_code(self.map_code)
        level_name = ""
        if self.map_level is not MISSING:
            self.map_level = preprocess_level_name(self.map_level)
            level_name = discord.utils.escape_markdown(self.map_level)

        embed = create_embed(
            title=f"Records for {self.map_code} {level_name}",
            desc="",
            user=self.interaction.user,
        )

        if self.map_code and self.map_level:
            records = await Record.filter_search(
                map_code=self.map_code,
                map_level=self.map_level,
                verified=True,
            )
            embeds = await split_embeds(embed, records, records_board_embed_fields)

        else:
            records = await Record.find_world_records(
                map_code=self.map_code, verified=True
            )
            embeds = await split_embeds(embed, records, records_wr_embed_fields)

        if not records:
            raise SearchNotFound("No records found.")

        view = Paginator(embeds, self.interaction.user)
        await view.start(self.interaction)


class WorldRecords(Slash, name="world-records"):
    """View a specific users world records."""

    user: discord.Member = discord.Option(
        description="Who's world records do you want to see?",
    )

    async def callback(self) -> None:
        await world_records(self.interaction, self.user)


class WorldRecordsShort(Slash, name="wr"):
    """View a specific users world records."""

    user: discord.Member = discord.Option(
        description="Who's world records do you want to see?",
    )

    async def callback(self) -> None:
        await world_records(self.interaction, self.user)


class WorldRecordsUserCommand(UserSlash, guilds=[GUILD_ID], name="world-records"):
    """View a specific users world records."""

    async def callback(self) -> None:
        await world_records(self.interaction, self.target)


class PersonalRecords(Slash, name="personal-records"):
    """View a specific users personal records."""

    user: discord.Member = discord.Option(
        description="Who's personal best do you want to see?",
    )

    async def callback(self) -> None:
        await personal_best(self.interaction, self.user)


class PersonalRecordsShort(Slash, name="pb"):
    """View a specific users personal records."""

    user: discord.Member = discord.Option(
        description="Who's personal best do you want to see?",
    )

    async def callback(self) -> None:
        await personal_best(self.interaction, self.user)


class PersonalRecordsUserCommand(UserSlash, guilds=[GUILD_ID], name="personal-records"):
    """View a specific users personal records."""

    async def callback(self) -> None:
        await personal_best(self.interaction, self.target)
