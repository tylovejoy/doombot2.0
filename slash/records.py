from logging import getLogger
from typing import Dict, Union, Optional

import discord
from discord import InteractionResponse
from discord.app import AutoCompleteResponse
from discord.utils import MISSING

from database.documents import ExperiencePoints
from database.records import Record
from slash.parents import SubmitParent, DeleteParent
from utils.constants import (
    GUILD_ID,
    VERIFICATION_CHANNEL_ID,
)
from utils.embed import (
    create_embed,
    records_basic_embed_fields,
    records_board_embed_fields,
    records_wr_embed_fields,
    records_wr_user_embed_fields,
    split_embeds,
    records_basic_embed_fields_verification,
)
from utils.enums import Emoji
from utils.records import delete_hidden
from utils.utilities import (
    find_alt_map_code,
    preprocess_map_code,
    time_convert,
    check_roles,
)
from views.records import RecordSubmitView, VerificationView, find_orig_msg
from views.paginator import Paginator

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(SubmitRecord)
    bot.application_command(DeleteRecord)
    bot.application_command(ViewRecords)
    bot.application_command(PersonalRecords)
    bot.application_command(PersonalRecordsUserCommand)


async def check_user(interaction):
    """Check if user exists, if not create a new user."""
    user = await ExperiencePoints.find_user(interaction.user.id)
    if not user:
        new_user = ExperiencePoints(
            user_id=interaction.user.id,
            alias=interaction.user.name,
            alerts_enabled=True,
        )
        await new_user.insert()
        return new_user
    return user


async def _autocomplete(focused, options):
    """Basic Autocomplete for Record slash commands."""
    if focused == "map_level":
        map_code = options.get("map_code")
        map_code = map_code.upper() if map_code else "NULL"
        levels = await Record.get_level_names(map_code)
        return AutoCompleteResponse({k: k for k in levels[:25]})
    if focused == "map_code":
        response = AutoCompleteResponse(
            {k: v for k, v in await Record.get_codes(options[focused])}
        )
        return response


class SubmitRecord(
    discord.SlashCommand, guilds=[GUILD_ID], name="record", parent=SubmitParent
):
    """Submit personal records to the database."""

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
        self.map_code = preprocess_map_code(self.map_code)
        self.map_code, code_changed = await find_alt_map_code(self.map_code)

        self.map_level = self.map_level.upper()

        # TODO: Attachment implementation

        record_seconds = time_convert(self.record)
        await check_user(self.interaction)

        record_document = await Record.filter_search(
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
            await self.interaction.response.send_message(
                "Personal best needs to be faster to update.", ephemeral=True
            )
            return

        # Create initial document if none found.
        if not record_document:
            record_document = Record(
                posted_by=self.interaction.user.id,
                code=self.map_code,
                level=self.map_level,
                verified=False,
                message_id=0,
                hidden_id=0,
            )

        record_document.record = record_seconds

        embed = create_embed(
            title="New submission", desc="", user=self.interaction.user
        )
        embed.add_field(**await records_basic_embed_fields(record_document))
        # TODO: Add image/attachment to embed
        # TODO: Find rank using $rank aggregation mongo 5.0 only
        view = RecordSubmitView()

        correct_msg = "Is this correct?"
        if code_changed:
            correct_msg = +f" **MAP CODE CHANGED TO ALIAS**"

        await self.interaction.response.send_message(
            correct_msg, ephemeral=True, view=view, embed=embed
        )
        await view.wait()

        if view.confirm.value:
            view.clear_items()
            await self.interaction.edit_original_message(
                content="Submitted.", view=view
            )
            # Delete old submission
            try:
                original = await find_orig_msg(self.interaction, record_document)
                await original.delete()
            except (discord.NotFound, discord.HTTPException):
                pass

            message = await self.interaction.channel.send(
                content=f"{Emoji.TIME} Waiting for verification...", embed=embed
            )
            record_document.message_id = message.id

            # Send verification notification.
            verification_channel = self.interaction.guild.get_channel(
                VERIFICATION_CHANNEL_ID
            )
            verify_view = VerificationView()
            hidden_msg = await verification_channel.send(embed=embed, view=verify_view)
            record_document.hidden_id = hidden_msg.id
            await record_document.save()

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        """Autocomplete for record submissions."""
        return await _autocomplete(focused, options)


class DeleteRecord(
    discord.SlashCommand, guilds=[GUILD_ID], name="record", parent=DeleteParent
):
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
        self.map_code = preprocess_map_code(self.map_code)
        self.map_level = self.map_level.upper()

        if self.user and check_roles(self.interaction):
            user_id = self.user.id
        else:
            user_id = self.interaction.user.id

        record_document = await Record.find_record(
            self.map_code, self.map_level, user_id
        )

        embed = create_embed(title="Delete Record", desc="", user=self.interaction.user)
        embed.add_field(**await records_basic_embed_fields(record_document))

        view = RecordSubmitView()
        await self.interaction.response.send_message(
            "Do you want to delete this?", ephemeral=True, view=view, embed=embed
        )
        await view.wait()

        if view.confirm.value:
            view.clear_items()
            await self.interaction.edit_original_message(content="Deleted.", view=view)
            await delete_hidden(self.interaction, record_document)
            await record_document.delete()

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        """Autocomplete for record deletion."""
        return await _autocomplete(focused, options)


class ViewRecords(discord.SlashCommand, guilds=[GUILD_ID], name="records"):
    """View personal records."""

    map_code: str = discord.Option(
        description="Workshop code to search for.",
        autocomplete=True,
    )
    map_level: Optional[str] = discord.Option(
        description="Level name to search for. Leave blank if you want to view world records for a specific map code.",
        autocomplete=True,
    )

    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        if self.map_level:
            self.map_level = self.map_level.upper()

        embed = create_embed(
            title=f"Records for {self.map_code} {self.map_level}",
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

        if self.map_code and not self.map_level:
            records = await Record.find_world_records(
                map_code=self.map_code, verified=True
            )
            embeds = await split_embeds(embed, records, records_wr_embed_fields)

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
        """Autocomplete for record viewing."""
        return await _autocomplete(focused, options)


class PersonalRecords(discord.SlashCommand, guilds=[GUILD_ID], name="personalrecords"):
    """View personal records."""

    world_records: bool = discord.Option(
        description="Show only your world records?",
    )

    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)
        embed = create_embed(
            title=f"Personal Bests", desc="", user=self.interaction.user
        )

        if self.world_records:
            records = await Record.find_world_records_user(self.interaction.user.id)
            embeds = await split_embeds(embed, records, records_wr_user_embed_fields)
        else:
            records = await Record.filter_search(
                user_id=self.interaction.user.id, verifed=True
            )
            embeds = await split_embeds(embed, records, records_basic_embed_fields)

        view = Paginator(embeds, self.interaction.user, timeout=None)
        await self.interaction.edit_original_message(
            embed=view.formatted_pages[0], view=view
        )
        await view.wait()


class PersonalRecordsUserCommand(
    discord.UserCommand, guilds=[GUILD_ID], name="personalbest"
):
    """Get personal bests of a specific user."""

    async def callback(self) -> None:
        await self.interaction.response.defer(ephemeral=True)
        embed = create_embed(title=f"Personal Bests", desc="", user=self.target)

        records = await Record.filter_search(user_id=self.target.id, verifed=False)
        embeds = await split_embeds(
            embed, records, records_basic_embed_fields_verification
        )

        view = Paginator(embeds, self.interaction.user, timeout=None)
        await self.interaction.edit_original_message(
            embed=view.formatted_pages[0],
            view=view,
        )
        await view.wait()
