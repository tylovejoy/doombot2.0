from logging import getLogger
from typing import Optional

import discord
from discord.utils import MISSING

from database.maps import Map, MapAlias
from slash.parents import DeleteParent, EditParent, SubmitParent
from slash.slash_command import MapSlash
from utils.constants import GUILD_ID, MAP_MAKER_ID, NEWEST_MAPS_ID
from utils.embed import create_embed, maps_embed_fields, split_embeds
from utils.enums import MapNames, MapTypes
from utils.errors import InvalidMapName, SearchNotFound, InvalidMapFilters
from utils.utilities import check_permissions, logging_util, preprocess_map_code
from views.basic import ConfirmButton
from views.maps import MapSubmitView
from views.paginator import Paginator

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "MAPS"))
    bot.application_command(MapSearch)
    bot.application_command(RandomMap)


class MapSearch(MapSlash, name="map-search"):
    """Search for maps using filters. You must use at least one filter."""

    map_name: Optional[str] = discord.Option(
        description="Name of a particular Overwatch map.",
        autocomplete=True,
    )
    map_type: Optional[str] = discord.Option(
        description="A specific type of map.",
        autocomplete=True,
    )
    creator: Optional[str] = discord.Option(
        description="Name of a specific creator. Separate multiple creators with commas."
    )


    async def callback(self) -> None:
        """Callback for map search slash command."""
        await self.defer(ephemeral=True)

        if all([x is MISSING for x in [self.map_name, self.map_type, self.creator]]):
            raise InvalidMapFilters(
                "You must have at least one map search filter e.g. map_type, map_name, or creator"
            )

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
            raise SearchNotFound("Nothing found with the selected filters.")

        embed = create_embed(title="Map Search", desc="", user=self.interaction.user)
        embeds = await split_embeds(embed, search, maps_embed_fields)

        view = Paginator(embeds, self.interaction.user)
        await view.start(self.interaction)


class SubmitMap(MapSlash, guilds=[GUILD_ID], parent=SubmitParent, name="map"):
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

        self.map_name = MapNames.fuzz(self.map_name)
        if self.map_name not in MapNames.list():
            raise InvalidMapName("Invalid map name!")

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


class DeleteMap(MapSlash, guilds=[GUILD_ID], name="map", parent=DeleteParent):
    """Delete a map from the database."""

    map_code: str = discord.Option(
        description="Workshop code for this parkour map.",
        autocomplete=True,
    )

    async def callback(self) -> None:
        """Callback for deleting a map slash command."""
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        await Map.check_code(self.map_code)
        map_document = await Map.find_one_map(self.map_code)
        await check_permissions(
            self.interaction, self.interaction.user.id == map_document.user_id
        )

        preview = (
            f"**Map Code:** {map_document.code}\n"
            f"**Map Name:** {map_document.map_name}\n"
            f"**Creator(s):** {map_document.creator}\n"
            f"**Description:** {map_document.description}\n"
            f"**Map Types:** {', '.join(map_document.map_type)}\n"
        )

        view = MapSubmitView(self.interaction, confirm_disabled=False)
        view.remove_item(view.select_menu)

        await self.interaction.edit_original_message(content=preview, view=view)

        await view.wait()
        if not view.confirm.value:
            return

        view.clear_items()
        preview += f"{'―' * 15}\n" "**__MAP DELETED__** from the database!"
        await map_document.delete()
        await self.interaction.edit_original_message(content=preview, view=view)


class EditMap(MapSlash, guilds=[GUILD_ID], name="map", parent=EditParent):
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
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)

        if self.new_map_code:
            self.new_map_code = preprocess_map_code(self.new_map_code)
        await Map.check_code(self.map_code)

        if self.map_name:
            self.map_name = MapNames.fuzz(self.map_name)
        map_document = await Map.find_one_map(self.map_code)

        await check_permissions(
            self.interaction, self.interaction.user.id == map_document.user_id
        )

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

        await self.interaction.edit_original_message(content=preview, view=view)

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


class RandomMap(MapSlash, name="random_map"):
    """Find random maps."""

    number: Optional[int] = discord.Option(
        description="How many random maps to find? default: 1", default=1
    )

    async def callback(self) -> None:
        """Callback for random map slash command."""
        await self.defer(ephemeral=True)
        search = await Map.random(self.number or 1)

        embed = create_embed(
            title="Map Search (Random)", desc="", user=self.interaction.user
        )
        embeds = await split_embeds(embed, search, maps_embed_fields)

        view = Paginator(embeds, self.interaction.user)
        await view.start(self.interaction)


class SubmitMapAlias(
    MapSlash, guilds=[GUILD_ID], name="map-alias", parent=SubmitParent
):
    """Create an alias for a map code. For when multiple codes point to the same map."""

    original_code: str = discord.Option(
        description="Original map code you want to create an alias for.",
        autocomplete=True,
    )
    alias: str = discord.Option(description="Alias for the original map code.")

    async def callback(self) -> None:
        self.original_code = preprocess_map_code(self.original_code)
        self.alias = preprocess_map_code(self.alias)

        document = MapAlias(alias=self.alias, original_code=self.original_code)

        view = discord.ui.View(timeout=None)
        confirm = ConfirmButton()
        view.add_item(confirm)

        string = (
            f"Original code: {self.original_code}\n"
            f"Alias: {self.alias}\n"
            f"Example: For records submitted with {self.alias}, will truly be submitted for {self.original_code}"
        )

        await self.interaction.response.send_message(string, view=view, ephemeral=True)
        await view.wait()

        if not confirm.value:
            return

        await document.insert()
        view.clear_items()
        await self.interaction.edit_original_message(content="Submitted.", view=view)
