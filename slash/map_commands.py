from logging import getLogger
from typing import Dict, Optional, Union
import discord
from discord import enums
from discord.app import AutoCompleteResponse
from database.documents import Map
from utils.embed import create_embed, maps_embed_fields, split_embeds

from utils.enum import MapNames, MapTypes
from views.maps import MapSubmitView
from views.paginator import Paginator


logger = getLogger(__name__)

MAPS_AUTOCOMPLETE = {k: k for k in MapNames.list()}
MAP_TYPES_AUTOCOMPLETE = {k: k for k in MapTypes.list()}


def setup(bot):
    bot.application_command(maps)
    bot.application_command(submitmap)


def preprocess_map_code(map_code):
    return map_code.upper().replace("O", "0")


def autocomplete_maps(options, focused):
    case = lambda x: x.casefold().startswith(options[focused].casefold())
    if focused == "map_name":

        if options[focused] == "":
            return AutoCompleteResponse({k: k for k in MapNames.list()[:25]})

        keys = {k: k for k in MAPS_AUTOCOMPLETE if case(k)}

        response = AutoCompleteResponse()
        for k in keys:
            response.add_option(k, k)

        return response

    if focused == "map_type":
        response = AutoCompleteResponse()
        keys = {k: k for k in MAP_TYPES_AUTOCOMPLETE if case(k)}
        for k in keys:
            response.add_option(k, k)

        return response


class maps(discord.SlashCommand, guilds=[195387617972322306]):
    """Search for maps using filters."""

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

        search = await Map.filter_search(
            map_name=self.map_name,
            map_type=self.map_type,
            creator=self.creator,
        )

        if not search:
            await self.interaction.response.send_message(
                content="Nothing found with the selected filters.", ephemeral=True
            )
            return

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

        return autocomplete_maps(options, focused)


class submitmap(discord.SlashCommand, guilds=[195387617972322306]):
    """Submit maps to the database."""

    map_code: str = discord.Option(
        description="Workshop code for this parkour map.",
    )
    map_name: str = discord.Option(
        description="Name of a particular Overwatch map.",
        autocomplete=True,
    )
    creator: str = discord.Option(description="Creator(s) of the map.")
    description: str = discord.Option(
        description="Description of the map. (How many levels, special features, etc.)"
    )

    async def callback(self) -> None:
        self.map_code = preprocess_map_code(self.map_code)

        if Map.check_code(self.map_code):
            await self.interaction.response.send_message(
                content="This workshop code already exists in the database!", ephemeral=True,
            )
            return

        preview = (
            f"**Map Code:** {self.map_code}\n"
            f"**Map Name:** {self.map_name}\n"
            f"**Creator(s):** {self.creator}\n"
            f"**Description:** {self.description}\n"
        )

        view = MapSubmitView()
        await self.interaction.response.send_message(
            content=preview, ephemeral=True, view=view
        )
        await view.wait()
        if view.confirm.value:
            view.clear_items()
            preview += (
                f"**Map Types:** {', '.join(view.select_menu.values)}\n"
                f"{'―' * 15}\n"
                "**__SUBMISSION CONFIRMED__** and submitted to the database!"
            )

            submission = Map(
                user_id=self.interaction.user.id,
                code=self.map_code,
                creator=self.creator,
                description=self.description,
                map_name=self.map_name,
                map_type=view.select_menu.values,
            )
            await submission.insert()
            await self.interaction.edit_original_message(content=preview, view=view)

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):

        return autocomplete_maps(options, focused)
