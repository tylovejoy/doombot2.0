from typing import Awaitable, List, Union

import discord

from database.documents import ExperiencePoints
from database.maps import Map
from database.records import Record
from utils.enums import Emoji
from utils.utilities import display_record


def create_embed(title: str, desc: str, user: discord.Member, color: hex = 0x000001):
    """Create a standardized embed."""
    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_author(name=user, icon_url=user.avatar.url)

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/app-icons/801483463642841150/4316132ab7deebe9b1bc93fc2fea576b.png"
    )
    return embed


async def maps_embed_fields(m: Map, *args) -> dict:
    """Embed fields for a map."""
    return {
        "name": f"{m.code} - {m.map_name}",
        "value": (
            f"> **Creator(s):** {m.creator}\n"
            f"> **Map Type(s):** {', '.join(m.map_type)}\n"
            f"> **Description:** {m.description}"
        ),
    }


async def records_board_embed_fields(r: Record, count: int) -> dict:
    """Embed fields for a record board."""
    return {
        "name": f"#{count + 1} - {await ExperiencePoints.get_alias(r.posted_by)}",
        "value": (
            f"> **Record**: {display_record(r.record)}\n"
            f"> **Verified**: {Emoji.is_verified(r.verified)}"
        ),
    }


async def records_basic_embed_fields(r: Record, *args) -> dict:
    """Embed fields for record submissions."""
    return {
        "name": f"{await ExperiencePoints.get_alias(r.posted_by)}",
        "value": (
            f"> **Map Code:** {r.code}\n"
            f"> **Level name:** {r.level}\n"
            f"> **Record:** {display_record(r.record)}\n"
        ),
    }


async def records_wr_embed_fields(r: Record, *args) -> dict:
    """Embed fields for world records among multiple levels."""
    return {
        "name": f"{r.id.level} - {await ExperiencePoints.get_alias(r.posted_by)}",
        "value": f"> **Record**: {display_record(r.record)}\n",
    }


async def records_wr_user_embed_fields(r: Record, *args) -> dict:
    """Embed fields for world records among multiple levels."""
    return {
        "name": f"{r.id.code} - {r.id.level} - {await ExperiencePoints.get_alias(r.posted_by)}",
        "value": f"> **Record**: {display_record(r.record)}\n",
    }


async def split_embeds(
    initial_embed: discord.Embed,
    documents: List[Union[Map, Record]],
    field_opts: Awaitable,
) -> List[discord.Embed]:
    """Split data into multiple embeds."""
    embed = initial_embed.copy()
    embeds = []
    count = len(documents)
    for i, doc in enumerate(documents):
        embed.add_field(**await field_opts(doc, i), inline=False)

        if i != 0 and ((i + 1) % 10 == 0 or count - 1 == i):
            embeds.append(embed)
            embed = initial_embed

        if count == 1:
            embeds.append(embed)

    return embeds
