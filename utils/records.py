import re

import discord

from database.records import Record
from utils.constants import VERIFICATION_CHANNEL_ID
from utils.embed import create_embed, split_embeds, records_wr_user_embed_fields
from utils.enums import Emoji
from utils.utilities import display_record
from views.paginator import Paginator


async def delete_hidden(interaction, record_document):
    """Try to delete hidden verification message."""
    try:
        hidden_msg = await interaction.guild.get_channel(
            VERIFICATION_CHANNEL_ID
        ).fetch_message(record_document.hidden_id)
        await hidden_msg.delete()
    except (discord.NotFound, discord.HTTPException):
        pass


async def world_records(interaction, target):
    await interaction.response.defer(ephemeral=True)

    embed = create_embed(title=f"World Records", desc="", user=target)
    records = await Record.find_world_records_user(target.id)
    embeds = await split_embeds(embed, records, records_wr_user_embed_fields)

    view = Paginator(embeds, interaction.user, timeout=None)
    await interaction.edit_original_message(
        embed=view.formatted_pages[0],
        view=view,
    )
    await view.wait()


async def personal_best(interaction, target):
    await interaction.response.defer(ephemeral=True)
    records = await Record.find_rec_map_info(user_id=target.id)
    embed = create_embed(title=f"Personal Bests", desc="", user=target)
    embed_dict = {}
    cur_map = None

    for r in records:
        if r.code != cur_map:
            cur_map = r.code
            creator = getattr(getattr(r, "map_data", None), "creator", None)
            map_name = getattr(getattr(r, "map_data", None), "map_name", None)

            if creator is None or map_name is None:
                creator = map_name = "N/A"

        if embed_dict.get(str(r.code), None) is None:
            embed_dict[str(r.code)] = {
                "title": f"{r.code} - {map_name} by {creator}\n",
                "value": "",
            }
        embed_dict[str(r.code)]["value"] += (
            f"> **{r.level}**\n"
            f"> Record: {display_record(r.record)}\n"
            f"> Verified: {Emoji.is_verified(r.verified)}\n"
            f"━━━━━━━━━━━━\n"
        )

    embeds = []

    if len(embed_dict) > 0:
        for i, map_pbs in enumerate(embed_dict.values()):
            if len(map_pbs["value"]) > 1024:
                # if over 1024 char limit
                # split pbs dict value into list of individual pbs
                # and divide in half.. Add two fields instead of just one.
                delimiter_regex = r">.*\n>.*\n>.*\n━━━━━━━━━━━━\n"
                pb_split = re.findall(delimiter_regex, map_pbs["value"])
                # pb_split = natsorted(pb_split)
                pb_split_1 = pb_split[: len(pb_split) // 2]
                pb_split_2 = pb_split[len(pb_split) // 2 :]
                embed.add_field(
                    name=f"{map_pbs['title']} (1)",
                    value="".join(pb_split_1),
                    inline=False,
                )
                embed.add_field(
                    name=f"{map_pbs['title']} (2)",
                    value="".join(pb_split_2),
                    inline=False,
                )
            else:
                embed.add_field(
                    name=map_pbs["title"], value=map_pbs["value"], inline=False
                )
            if (i + 1) % 3 == 0 or (i + 1) == len(embed_dict):
                embeds.append(embed)
                embed = discord.Embed(title=target.name)

    view = Paginator(embeds, interaction.user, timeout=None)
    await interaction.edit_original_message(
        embed=view.formatted_pages[0],
        view=view,
    )
    await view.wait()
