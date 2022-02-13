from typing import List, Union

import discord
from discord.utils import MISSING

from database.documents import ExperiencePoints
from database.maps import Map
from database.records import Record, WorldRecordsAggregate
from database.tournament import TournamentRecordsLookup
from utils.enums import Emoji
from utils.utilities import display_record


def create_embed(
    title: str,
    desc: str,
    user: Union[discord.Member, discord.User, str],
    color: hex = 0x000001,
) -> discord.Embed:
    """Create a standardized embed."""
    embed = discord.Embed(title=title, description=desc, color=color)
    if not isinstance(user, str):
        embed.set_author(name=user.name, icon_url=user.avatar.url)
    else:
        embed.set_author(name=user)

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/app-icons/801483463642841150/4316132ab7deebe9b1bc93fc2fea576b.png"
    )
    return embed


def hall_of_fame(title: str, desc: str = "") -> discord.Embed:
    embed = discord.Embed(title=title, description=desc, color=0xF7BD00)
    embed.set_author(name="Hall of Fame")
    embed.set_thumbnail(url="https://clipartart.com/images/dog-trophy-clipart-2.png")
    return embed


async def maps_embed_fields(m: Map, *args, **kwargs) -> dict:
    """Embed fields for a map."""
    return {
        "name": f"{m.code} - {m.map_name}",
        "value": (
            f"> **Creator(s):** {m.creator}\n"
            f"> **Map Type(s):** {', '.join(m.map_type)}\n"
            f"> **Description:** {m.description}"
        ),
    }


async def records_tournament_embed_fields(
    r: TournamentRecordsLookup, count: int, category=None, rank=None
) -> Union[dict, None]:
    cat = getattr(r, category, None)
    if not cat:
        return
    rank_emoji = {
        "Unranked": "Unranked",
        "Gold": discord.PartialEmoji.from_str("<:gold:931317421862699118>"),
        "Diamond": discord.PartialEmoji.from_str("<:diamond:931317455639445524>"),
        "Grandmaster": discord.PartialEmoji.from_str(
            "<:grandmaster:931317469396729876>"
        ),
    }
    rank_str = ""

    if getattr(r, "user_data", None):
        alias = r.user_data.alias
        if rank is MISSING:
            rank_str = r.user_data.rank
            rank_str = getattr(rank_str, category)
            rank_str = rank_emoji[rank_str]
    else:
        alias = "Unknown user"
        rank_str = " - Unknown rank"

    return {
        "name": f"#{count + 1} - {alias}{rank_str}",
        "value": f"> **Record**: {display_record(cat.records.record)}\n",
    }


async def records_board_embed_fields(r: Record, count: int, *args, **kwargs) -> dict:
    """Embed fields for a record board."""
    return {
        "name": f"#{count + 1} - {await ExperiencePoints.get_alias(r.user_id)}",
        "value": (
            f"> **Record**: {display_record(r.record)}\n"
            f"> **Verified**: {Emoji.is_verified(r.verified)}\n"
            f'> [Image Link]({r.attachment_url} "Link to the original submission image.")'
        ),
    }


async def records_basic_embed_fields(r: Record, *args, **kwargs) -> dict:
    """Embed fields for record submissions."""
    return {
        "name": f"{await ExperiencePoints.get_alias(r.user_id)}",
        "value": (
            f"> **Map Code:** {r.code}\n"
            f"> **Level name:** {discord.utils.escape_markdown(r.level)}\n"
            f"> **Record:** {display_record(r.record)}\n"
            f'> [Image Link]({r.attachment_url} "Link to the original submission image.")'
        ),
    }


async def records_basic_embed_fields_verification(r: Record, *args, **kwargs) -> dict:
    """Embed fields for record submissions."""
    return {
        "name": f"{await ExperiencePoints.get_alias(r.user_id)}",
        "value": (
            f"> **Map Code:** {r.code}\n"
            f"> **Level name:** {discord.utils.escape_markdown(r.level)}\n"
            f"> **Record:** {display_record(r.record)}\n"
            f"> **Verified**: {Emoji.is_verified(r.verified)}\n"
            f'> [Image Link]({r.attachment_url} "Link to the original submission image.")'
        ),
    }


async def records_wr_embed_fields(r: Record, *args, **kwargs) -> dict:
    """Embed fields for world records among multiple levels."""
    return {
        "name": f"{discord.utils.escape_markdown(r.id.level)} - {await ExperiencePoints.get_alias(r.user_id)}",
        "value": (
            f"> **Record**: {display_record(r.record)}\n"
            f'> [Image Link]({r.attachment_url} "Link to the original submission image.")'
        ),
    }


async def records_wr_user_embed_fields(r: Record, *args, **kwargs) -> dict:
    """Embed fields for world records among multiple levels."""
    return {
        "name": (
            f"{r.id.code} - {discord.utils.escape_markdown(r.id.level)} - {await ExperiencePoints.get_alias(r.user_id)}"
        ),
        "value": (
            f"> **Record**: {display_record(r.record)}\n"
            f'> [Image Link]({r.attachment_url} "Link to the original submission image.")'
        ),
    }


async def split_embeds(
    initial_embed: discord.Embed,
    documents: List[Union[Map, Record, WorldRecordsAggregate, TournamentRecordsLookup]],
    field_opts,
    category=None,
    rank=None,
) -> List[discord.Embed]:
    """Split data into multiple embeds."""
    embed = initial_embed.copy()
    embeds = []
    count = len(documents)
    for i, doc in enumerate(documents):
        embed.add_field(
            **await field_opts(doc, i, category=category, rank=rank), inline=False
        )

        if i != 0 and ((i + 1) % 10 == 0 or count - 1 == i):
            embeds.append(embed)
            embed = initial_embed.copy()

        if count == 1:
            embeds.append(embed)

    return embeds
