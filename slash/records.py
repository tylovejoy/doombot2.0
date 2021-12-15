from logging import getLogger
from typing import Dict, Union

import discord
from discord.app import AutoCompleteResponse
from database.documents import ExperiencePoints
from database.records import Record
from slash.parents import SubmitParent
from utils.constants import GUILD_ID, VERIFICATION_CHANNEL_ID
from utils.embed import create_embed, records_basic_embed_fields
from utils.enum import Emoji
from utils.utils import preprocess_map_code, time_convert
from views.records import RecordSubmitView, VerificationView, find_orig_msg

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(SubmitRecord)
    bot.application_command(Test)


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
        self.map_level = self.map_level.upper()

        # TODO: Attachment implementation

        record_seconds = time_convert(self.record)
        await check_user(self.interaction)

        record_document = await Record.find_record(
            self.map_code, self.map_level, self.interaction.user.id
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
        await self.interaction.response.send_message(
            "Is this correct?", ephemeral=True, view=view, embed=embed
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


class Test(discord.SlashCommand, guilds=[GUILD_ID], name="test"):

    """test"""

    async def callback(self) -> None:
        pass
