import math
import re

import discord

from database.documents import VerificationViews
from database.records import Record
from utils.constants import VERIFICATION_CHANNEL_ID
from utils.embed import create_embed, records_wr_user_embed_fields, split_embeds
from utils.enums import Emoji
from utils.utilities import display_record
from views.paginator import Paginator


async def delete_hidden(interaction: discord.Interaction, record_document: Record):
    """Try to delete hidden verification message."""
    try:
        hidden_msg = await interaction.guild.get_channel(
            VERIFICATION_CHANNEL_ID
        ).fetch_message(record_document.hidden_id)
        await VerificationViews.find_one(
            VerificationViews.message_id == record_document.hidden_id
        ).delete()
        await hidden_msg.delete()
    except (discord.NotFound, discord.HTTPException):
        pass


async def world_records(interaction: discord.Interaction, target: discord.Member):
    """Find and display world records of a specific member."""
    await interaction.response.defer(ephemeral=True)

    embed = create_embed(title="World Records", desc="", user=target)
    records = await Record.find_world_records_user(target.id)
    if not records:
        await interaction.edit_original_message(content="No records found.")
        return

    embeds = await split_embeds(embed, records, records_wr_user_embed_fields)

    view = Paginator(embeds, interaction.user)
    await view.start(interaction)


async def personal_best(interaction: discord.Interaction, target: discord.Member):
    """Find and display personal bests of a specific member."""
    await interaction.response.defer(ephemeral=True)
    records = await Record.find_rec_map_info(user_id=target.id)
    if not records:
        await interaction.edit_original_message(content="No records found.")
        return

    embed = create_embed(title="Personal Bests", desc="", user=target)
    embed_dict = {}
    cur_map = None
    map_name, creator = None, None
    for r in records:
        if r.code != cur_map:
            cur_map = r.code
            creator = getattr(getattr(r, "map_data", None), "creator", "N/A")
            map_name = getattr(getattr(r, "map_data", None), "map_name", "N/A")

        if embed_dict.get(r.code) is None:
            embed_dict[r.code] = {
                "title": f"{r.code} - {map_name} by {creator}\n",
                "value": "",
            }
        embed_dict[r.code]["value"] += (
            f"> **{discord.utils.escape_markdown(r.level)}**\n"
            f"> Record: {display_record(r.record)}\n"
            f"> Verified: {Emoji.is_verified(r.verified)}\n"
            f"━━━━━━━━━━━━\n"
        )

    embeds = []

    # if over 1024 char limit
    # split pbs dict value into list of individual pbs
    # and divide in half.. Add two fields instead of just one.
    if len(embed_dict) > 0:

        delimiter_regex = r">.*\n>.*\n>.*\n━━━━━━━━━━━━\n"

        for i, map_pbs in enumerate(embed_dict.values()):
            pb_split = re.findall(delimiter_regex, map_pbs["value"])
            splits_amount = (len(map_pbs["value"]) // 1024) + 1
            splits_length = math.ceil(len(pb_split) / splits_amount)

            chunks = [
                pb_split[splits_length * x : splits_length * (x + 1)]
                for x in range(int(len(pb_split) / splits_length + 1))
            ]

            for chunk in chunks:
                if len(chunk) > 0:
                    embed.add_field(
                        name=f"{map_pbs['title']}",
                        value="".join(chunk),
                        inline=False,
                    )

            if (i + 1) % 3 == 0 or (i + 1) == len(embed_dict):
                embeds.append(embed)
                embed = discord.Embed(title=target.name)

    view = Paginator(embeds, interaction.user)
    await view.start(interaction)
