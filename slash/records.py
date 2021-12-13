from logging import getLogger
from typing import Dict, Union, Optional, List

import discord
from discord.app import AutoCompleteResponse
from database.documents import Record, ExperiencePoints, WorldRecordsAggregate
from slash.parents import SubmitParent
from utils.constants import GUILD_ID
from utils.embed import create_embed, records_basic_embed_fields
from utils.utils import preprocess_map_code, time_convert
from views.records import RecordSubmitView

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(SubmitRecord)
    bot.application_command(Test)


async def check_user(interaction):
    """Check if user exists, if not create a new user."""
    if not await ExperiencePoints.user_exists(interaction.user.id):
        new_user = ExperiencePoints(
            user_id=interaction.user.id,
            alias=interaction.user.name,
            alerts_enabled=True,
        )
        await new_user.insert()
        return new_user
    return ExperiencePoints.find_user(interaction.user.id)


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
        self.map_code = preprocess_map_code(self.map_code)
        self.map_level = self.map_level.upper()

        # TODO: Attachment implementation

        record_seconds = time_convert(self.record)
        await check_user(self.interaction)

        record_document = await Record.find_record(
            self.map_code, self.map_level, self.interaction.user.id
        )

        if (
            record_document
            and record_document.verified
            and record_seconds >= record_document.record
        ):
            await self.interaction.response.send_message(
                "Personal best needs to be faster to update.", ephemeral=True
            )
            return

        if not record_document:
            record_document = Record(
                posted_by=self.interaction.user.id,
                code=self.map_code,
                level=self.map_level,
                record=record_seconds,
                verified=False,
                message_id=0,
                hidden_id=0,
            )

        embed = create_embed(
            title="New submission", desc="", user=self.interaction.user
        )
        embed.add_field(**await records_basic_embed_fields(record_document))
        # TODO: Add image/attachment to embed

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

            # TODO: Find rank using $rank aggregation mongo 5.0 only
            # TODO: Send to hidden verification channel.

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
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

    member: discord.Member = discord.Option(description="user id")

    async def callback(self) -> None:
        # x = await Record.find_world_records(int(self.member))
        # for i in x:
        #     print(i.id.code, i.id.level, i.record)
        print(type(self.member.id))
