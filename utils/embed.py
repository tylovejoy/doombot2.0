from typing import Callable, List, Optional, Union
import discord

from database.documents import ExperiencePoints, Map, Record
from utils.enum import Emoji
from utils.utils import display_record, get_user_name


def create_embed(title: str, desc: str, user: discord.Member, color: hex = 0x000001):
    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_author(name=user, icon_url=user.avatar.url)

    embed.set_thumbnail(
        url="https://cdn.discordapp.com/app-icons/801483463642841150/4316132ab7deebe9b1bc93fc2fea576b.png"
    )
    return embed


def maps_embed_fields(m: Map, *args) -> dict:
    return {
        "name": f"{m.code} - {m.map_name}",
        "value": (
            f"> Creator(s): {m.creator}\n"
            f"> Map Type(s): {', '.join(m.map_type)}\n"
            f"> Description: {m.description}"
        ),
    }


def records_embed_fields(r: Record, count: int) -> dict:
    return {
        "name": f"#{count} - {ExperiencePoints.get_alias(r.user_id)}",
        "value": (
            f"> Record: {display_record(r.record)}\n"
            f"> Verified: {Emoji.is_verified(r.verified)}"
        ),
    }


def split_embeds(
    initial_embed: discord.Embed,
    documents: List[Union[Map, Record]],
    field_opts: Callable,
) -> List[discord.Embed]:
    """Split data into multiple embeds."""
    embed = initial_embed.copy()
    embeds = []
    count = len(documents)
    for i, doc in enumerate(documents):
        embed.add_field(**field_opts(doc, i), inline=False)

        if i != 0 and ((i + 1) % 10 == 0 or count - 1 == i):
            embeds.append(embed)
            embed = initial_embed

        if count == 1:
            embeds.append(embed)

    return embeds
