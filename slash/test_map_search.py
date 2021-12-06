from typing import Dict, Optional, Union
import discord
from database.documents import Map
from utils.embed import create_embed, maps_embed_fields, split_embeds

from utils.enum import MapNames, MapTypes
from views.paginator import Paginator


def setup(bot):
    bot.application_command(maps)


class maps(discord.SlashCommand, guilds=[195387617972322306]):
    map_name: Optional[str] = discord.Option(
        description="Name of a particular Overwatch map.",
        autocomplete=True,
    )
    map_type: Optional[str] = discord.Option(
        description="A specific type of map.",
        autocomplete=True,
    )
    creator: Optional[str] = discord.Option(description="Name of a specific creator.")

    async def callback(self) -> None:
        fuzzy_name, fuzzy_type = None, None
        if self.map_name:
            fuzzy_name = MapNames.fuzz(self.map_name)
        if self.map_type:
            fuzzy_type = MapTypes.fuzz(self.map_type)

        search = await Map.filter_search(
            map_name=fuzzy_name,
            map_type=fuzzy_type,
            creator=self.creator,
        )

        embed = create_embed(title="Map Search", desc="", user=self.interaction.user)
        embeds = split_embeds(embed, search, maps_embed_fields)

        view = Paginator(embeds, self.interaction.user, timeout=None)
        await self.interaction.response.send_message(
            embed=view.formatted_pages[0], view=view, ephemeral=True
        )
        await view.wait()

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        if focused == "map_name":
            pass

        if focused == "map_type":
            pass
