from logging import getLogger
from typing import Dict, Optional, Union

import discord

from database.maps import Map, MapAlias
from slash.parents import SubmitParent, DeleteParent, EditParent
from utils.embed import (
    create_embed,
    maps_embed_fields,
    split_embeds,
)
from utils.constants import (
    GUILD_ID,
    NEWEST_MAPS_ID,
    MAP_MAKER_ID,
)
from utils.utilities import (
    logging_util,
    no_perms_warning,
    preprocess_map_code,
    case_ignore_compare,
    check_roles,
)
from utils.enums import (
    MapNames,
    MapTypes,
)

from views.basic import ConfirmButton
from views.maps import MapSubmitView
from views.paginator import Paginator

logger = getLogger(__name__)

MAPS_AUTOCOMPLETE = {k: k for k in MapNames.list()}
MAP_TYPES_AUTOCOMPLETE = {k: k for k in MapTypes.list()}


def setup(bot):
    logger.info(logging_util("Loading", "MAPS"))
    bot.application_command(MapSearch)
    bot.application_command(RandomMap)


def autocomplete_maps(options, focused):
    """Display autocomplete for map names and types."""
    if focused == "map_name":
        if options[focused] == "":
            return discord.AutoCompleteResponse({k: k for k in MapNames.list()[:25]})
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


class MapSearch(discord.SlashCommand, name="map-search"):
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
        """Callback for map search slash command."""
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

        if not search:
            await self.interaction.response.send_message(
                content="Nothing found with the selected filters.", ephemeral=True
            )
            return

        embed = create_embed(title="Map Search", desc="", user=self.interaction.user)
        embeds = await split_embeds(embed, search, maps_embed_fields)

        view = Paginator(embeds, self.interaction.user, timeout=None)
        await self.interaction.response.send_message(
            embed=view.formatted_pages[0], view=view, ephemeral=True
        )
        await view.wait()

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        """Autocomplete for slash command."""
        return autocomplete_maps(options, focused)


class SubmitMap(
    discord.SlashCommand, guilds=[GUILD_ID], parent=SubmitParent, name="map"
):
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
        """Callback for map submission slash command."""
        self.map_code = preprocess_map_code(self.map_code)

        if await Map.check_code(self.map_code):
            await self.interaction.response.send_message(
                content="This workshop code already exists in the database!",
                ephemeral=True,
            )
            return

        self.map_name = MapNames.fuzz(self.map_name)
        if self.map_name not in MapNames.list():
            await self.interaction.response.send_message(
                content="Invalid map name!",
                ephemeral=True,
            )
            return

        preview = (
            f"**Map Code:** {self.map_code}\n"
            f"**Map Name:** {self.map_name}\n"
            f"**Creator(s):** {self.creator}\n"
            f"**Description:** {self.description}\n"
        )

        view = MapSubmitView(self.interaction)
        await self.interaction.response.send_message(
            content=preview, ephemeral=True, view=view
        )

        await view.wait()
        if not view.confirm.value:
            return

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

        new_maps_channel = self.interaction.guild.get_channel(NEWEST_MAPS_ID)

        embed = create_embed(title="New Map!", desc="", user=self.interaction.user)
        embed.add_field(**await maps_embed_fields(submission), inline=False)

        new_map = await new_maps_channel.send(embed=embed)
        await new_map.create_thread(name=f"Discuss {self.map_code} here.")
        # Add map maker role
        map_maker_role = self.interaction.guild.get_role(MAP_MAKER_ID)
        if map_maker_role not in self.interaction.user.roles:
            await self.interaction.user.add_roles(
                map_maker_role,
                reason="User submitted a map to the bot.",
            )

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        """Autocomplete for map submission slash command."""
        return autocomplete_maps(options, focused)


class DeleteMap(
    discord.SlashCommand, guilds=[GUILD_ID], name="map", parent=DeleteParent
):
    """Delete a map from the database."""

    map_code: str = discord.Option(
        description="Workshop code for this parkour map.",
    )

    async def callback(self) -> None:
        """Callback for deleting a map slash command."""
        self.map_code = preprocess_map_code(self.map_code)

        if not await Map.check_code(self.map_code):
            await self.interaction.response.send_message(
                content="This workshop code doesn't exist in the database!",
                ephemeral=True,
            )
            return

        map_document = await Map.find_one_map(self.map_code)

        if (
            not check_roles(self.interaction)
            or self.interaction.user.id != map_document.user_id
        ):
            await no_perms_warning(self.interaction)
            return

        preview = (
            f"**Map Code:** {map_document.code}\n"
            f"**Map Name:** {map_document.map_name}\n"
            f"**Creator(s):** {map_document.creator}\n"
            f"**Description:** {map_document.description}\n"
            f"**Map Types:** {', '.join(map_document.map_type)}\n"
        )

        view = MapSubmitView(self.interaction, confirm_disabled=False)
        view.remove_item(view.select_menu)

        await self.interaction.response.send_message(
            content=preview, ephemeral=True, view=view
        )

        await view.wait()
        if not view.confirm.value:
            return

        view.clear_items()
        preview += f"{'―' * 15}\n" "**__MAP DELETED__** from the database!"
        await map_document.delete()
        await self.interaction.edit_original_message(content=preview, view=view)


class EditMap(discord.SlashCommand, guilds=[GUILD_ID], name="map", parent=EditParent):
    """Edit maps that you have submitted to the database. You can edit any field."""

    map_code: str = discord.Option(
        description="Workshop code for this parkour map.",
    )

    new_map_code: Optional[str] = discord.Option(
        description="New workshop code for this parkour map.",
    )

    map_name: Optional[str] = discord.Option(
        description="Name of a particular Overwatch map.",
        autocomplete=True,
    )
    creator: Optional[str] = discord.Option(description="Creator(s) of the map.")
    description: Optional[str] = discord.Option(
        description="Description of the map. (How many levels, special features, etc.)"
    )

    async def callback(self) -> None:
        """Callback for edit map slash command."""
        self.map_code = preprocess_map_code(self.map_code)

        if self.new_map_code:
            self.new_map_code = preprocess_map_code(self.new_map_code)
        if not await Map.check_code(self.map_code):
            await self.interaction.response.send_message(
                content="This workshop code doesn't exist in the database!",
                ephemeral=True,
            )
            return
        if self.map_name:
            self.map_name = MapNames.fuzz(self.map_name)
        map_document = await Map.find_one_map(self.map_code)

        if (
            not check_roles(self.interaction)
            or self.interaction.user.id != map_document.user_id
        ):
            await self.interaction.response.send_message(
                content="You do not have permission to edit this!",
                ephemeral=True,
            )
            return

        map_document.code = self.new_map_code or map_document.code
        map_document.map_name = self.map_name or map_document.map_name
        map_document.creator = self.creator or map_document.creator
        map_document.description = self.description or map_document.description

        preview = (
            f"**Map Code:** {map_document.code}\n"
            f"**Map Name:** {map_document.map_name}\n"
            f"**Creator(s):** {map_document.creator}\n"
            f"**Description:** {map_document.description}\n"
        )

        view = MapSubmitView(self.interaction, confirm_disabled=False)
        for x in view.select_menu.options:
            if x.label in map_document.map_type:
                x.default = True

        await self.interaction.response.send_message(
            content=preview, ephemeral=True, view=view
        )

        await view.wait()

        map_document.map_type = view.select_menu.values or map_document.map_type

        if not view.confirm.value:
            return

        view.clear_items()
        preview += (
            f"**Map Types:** {', '.join(view.select_menu.values)}\n"
            f"{'―' * 15}\n"
            "**__SUBMISSION CONFIRMED__** and submitted to the database!"
        )
        await map_document.save()
        await self.interaction.edit_original_message(content=preview, view=view)

    async def autocomplete(
        self, options: Dict[str, Union[int, float, str]], focused: str
    ):
        """Autocomplete for edit map slash command."""
        return autocomplete_maps(options, focused)


class RandomMap(discord.SlashCommand, name="random_map"):
    """Find random maps."""

    number: Optional[int] = discord.Option(
        description="How many random maps to find? default: 1", default=1
    )

    async def callback(self) -> None:
        """Callback for random map slash command."""
        search = await Map.random(self.number or 1)

        embed = create_embed(
            title="Map Search (Random)", desc="", user=self.interaction.user
        )
        embeds = await split_embeds(embed, search, maps_embed_fields)

        view = Paginator(embeds, self.interaction.user, timeout=None)
        await self.interaction.response.send_message(
            embed=view.formatted_pages[0], view=view, ephemeral=True
        )
        await view.wait()


class SubmitMapAlias(
    discord.SlashCommand, guilds=[GUILD_ID], name="map-alias", parent=SubmitParent
):
    """Create an alias for a map code. For when multiple codes point to the same map."""

    original_code: str = discord.Option(
        description="Original map code you want to create an alias for."
    )
    alias: str = discord.Option(description="Alias for the original map code.")

    async def callback(self) -> None:
        self.original_code = preprocess_map_code(self.original_code)
        self.alias = preprocess_map_code(self.alias)

        document = MapAlias(alias=self.alias, original_code=self.original_code)

        view = discord.ui.View(timeout=None)
        view.add_item(ConfirmButton())

        string = (
            f"Original code: {self.original_code}\n"
            f"Alias: {self.alias}\n"
            f"Example: For records submitted with {self.alias}, will truly be submitted for {self.original_code}"
        )

        await self.interaction.response.send_message(string, view=view, ephemeral=True)
        await view.wait()

        if not view.children[0].value:
            return

        await document.insert()
        view.clear_items()
        await self.interaction.edit_original_message(content="Submitted.", view=view)
