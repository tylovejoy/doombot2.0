from typing import List

from database.documents import Map


def split_map_embeds(initial_embed, maps: List[Map]):
    """Split map data into multiple embeds."""
    embed = initial_embed.copy()
    embeds = []
    count = len(maps)
    for i, m in enumerate(maps):
        embed.add_field(
            name=f"{m.code} - {m.map_name}",
            value=f"> Creator(s): {m.creator}\n> Map Type(s): {', '.join(m.map_type)}\n> Description: {m.description}",
            inline=False,
        )

        if i != 0 and ((i + 1) % 10 == 0 or count - 1 == i):
            embeds.append(embed)
            embed = initial_embed

        if count == 1:
            embeds.append(embed)

    return embeds
