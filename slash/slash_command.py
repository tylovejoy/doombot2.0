from typing import Dict, List, Union
import discord
from database.documents import Tags

from database.records import Record
from utils.enums import MapNames, MapTypes
from utils.utilities import case_ignore_compare


MAPS_AUTOCOMPLETE = {k: k for k in MapNames.list()}
MAP_TYPES_AUTOCOMPLETE = {k: k for k in MapTypes.list()}


class Slash(discord.SlashCommand):
    async def error(self, exception: Exception) -> None:
        await self.interaction.edit_original_message(
            content=exception,
        )


class UserSlash(discord.UserCommand):
    async def error(self, exception: Exception) -> None:
        await self.interaction.edit_original_message(
            content=exception,
        )


class MapSlash(Slash):
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> List:
        """Display autocomplete for map names and types."""
        if focused == "map_name":
            if options[focused] == "":
                return discord.AutoCompleteResponse(
                    {k: k for k in MapNames.list()[:25]}
                )
            response = discord.AutoCompleteResponse(
                {
                    k: k
                    for k in MAPS_AUTOCOMPLETE
                    if case_ignore_compare(k, options[focused])
                }
            )
            return response

        if focused == "map_type":
            response = discord.AutoCompleteResponse(
                {
                    k: k
                    for k in MAP_TYPES_AUTOCOMPLETE
                    if case_ignore_compare(k, options[focused])
                }
            )
            return response


class RecordSlash(Slash):
    async def autocomplete(focused, options):
        """Basic Autocomplete for Record slash commands."""
        if focused == "map_level":
            map_code = options.get("map_code")
            map_code = map_code.upper() if map_code else "NULL"
            levels = await Record.get_level_names(map_code)
            return discord.AutoCompleteResponse({k: k for k in levels[:25]})
        if focused == "map_code":
            response = discord.AutoCompleteResponse(
                {k: v for k, v in await Record.get_codes(options[focused])}
            )
            return response


class TagSlash(Slash):
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> List:
        tag_names = await Tags.find_all_tag_names()
        return await tags_autocomplete(options, focused, tag_names)


class WorkshopSlash(Slash):
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> List:
        return await tags_autocomplete(options, focused, self.client.ws_list)


async def tags_autocomplete(
    options: Dict[str, Union[int, float, str]], focused: str, list_obj: List
):
    if options[focused] == "":
        return discord.AutoCompleteResponse({k: k for k in list_obj[:25]})

    if focused in ["name", "search"]:
        count = 0
        autocomplete_ = {}
        for k in list_obj:
            if case_ignore_compare(k, options[focused]) and count < 25:
                autocomplete_[k] = k
                count += 1

        return discord.AutoCompleteResponse(autocomplete_)
