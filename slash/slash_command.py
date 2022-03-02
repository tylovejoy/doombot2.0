import io
import traceback
from typing import Dict, List, Union

import discord
from utils.constants import ERROR_LOGS

from database.documents import Tags
from database.records import Record
from utils.errors import DoombotBaseException
from utils.enums import MapNames, MapTypes
from utils.utilities import case_ignore_compare

MAPS_AUTOCOMPLETE = {k: k for k in MapNames.list()}
MAP_TYPES_AUTOCOMPLETE = {k: k for k in MapTypes.list()}


class Slash(discord.SlashCommand):
    async def error(self, exception: Exception) -> None:
        if isinstance(exception, DoombotBaseException):
            if self.interaction.response.is_done():
                await self.interaction.edit_original_message(
                    content=exception,
                )
            else:
                await self.send(
                    content=exception,
                )
        else:
            channel = self.client.get_channel(ERROR_LOGS)
            if (
                len(
                    "".join(
                        traceback.format_exception(
                            None, exception, exception.__traceback__
                        )
                    )
                )
                < 1850
            ):
                await channel.send(
                    f"**Error: {self._name_}**\n"
                    f"Channel: `{self.interaction.channel}`"
                    f"User: `{self.interaction.user}`\n```\n"
                    + "".join(
                        traceback.format_exception(
                            None, exception, exception.__traceback__
                        )
                    )
                    + "\n```"
                )
            else:
                await channel.send(
                    f"**Error: {self._name_}**\n"
                    f"Channel: `{self.interaction.channel}`"
                    f"User: `{self.interaction.user}`" + "\n",
                    file=discord.File(
                        fp=io.BytesIO(exception.encode(errors="ignore")),
                        filename="error.log",
                    ),
                )


class UserSlash(discord.UserCommand):
    async def error(self, exception: Exception) -> None:
        await self.interaction.edit_original_message(
            content=str(exception),
        )


class MapSlash(Slash):
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> discord.AutoCompleteResponse:
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
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> discord.AutoCompleteResponse:
        """Basic Autocomplete for Record slash commands."""
        if focused == "map_level":
            map_code = options.get("map_code")
            map_code = map_code.upper() if map_code else "NULL"
            levels = await Record.get_level_names(map_code)
            return discord.AutoCompleteResponse({k: k for k in levels[:25]})
        if focused == "map_code":
            return discord.AutoCompleteResponse(
                {k: v for k, v in await Record.get_codes(options[focused])}
            )


class TagSlash(Slash):
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> discord.AutoCompleteResponse:
        tag_names = await Tags.find_all_tag_names()
        return await tags_autocomplete(options, focused, tag_names)


class WorkshopSlash(Slash):
    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ) -> discord.AutoCompleteResponse:
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
