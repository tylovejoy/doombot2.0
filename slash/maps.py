from logging import getLogger
from typing import Dict, Optional, Union
import discord
from discord.app import AutoCompleteResponse
from database.documents import Map
from slash.parents import SubmitParent, DeleteParent, EditParent
from utils.embed import create_embed, maps_embed_fields, split_embeds
from utils.constants import ROLE_WHITELIST, GUILD_ID, NEWEST_MAPS_ID
from utils.enum import MapNames, MapTypes
from utils.utils import preprocess_map_code, case_ignore_compare
from views.maps import MapSubmitView
from views.paginator import Paginator


logger = getLogger(__name__)

MAPS_AUTOCOMPLETE = {k: k for k in MapNames.list()}
MAP_TYPES_AUTOCOMPLETE = {k: k for k in MapTypes.list()}


def setup(bot):
    bot.application_command(MapSearch)
    bot.application_command(SubmitMap)
    bot.application_command(EditMap)
    bot.application_command(RandomMap)
    bot.application_command(DeleteMap)


def autocomplete_maps(options, focused):
    """Display autocomplete for map names and types."""
    if focused == "map_name":
        if options[focused] == "":
            return AutoCompleteResponse({k: k for k in MapNames.list()[:25]})
        response = AutoCompleteResponse(
            {
                k: k
                for k in MAPS_AUTOCOMPLETE
                if case_ignore_compare(k, options[focused])
            }
        )
        return response

    if focused == "map_type":
        response = AutoCompleteResponse(
            {
                k: k
                for k in MAP_TYPES_AUTOCOMPLETE
                if case_ignore_compare(k, options[focused])
            }
        )
        return response


class MapSearch(discord.SlashCommand, guilds=[GUILD_ID], name="map_search"):
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
        embeds = split_embeds(embed, search, maps_embed_fields)

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
        await self.client.wait_for("interaction")

        for x in view.select_menu.options:
            if x.label in view.select_menu.values:
                x.default = True

        await self.interaction.edit_original_message(view=view)
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

            new_maps_channel = self.interaction.guild.get_channel(NEWEST_MAPS_ID)

            embed = create_embed(title="New Map!", desc="", user=self.interaction.user)
            embed.add_field(**maps_embed_fields(submission), inline=False)

            new_map = await new_maps_channel.send(embed=embed)
            await new_map.create_thread(name=f"Discuss {self.map_code} here.")

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

        if self.interaction.user.id != map_document.user_id and not any(
            role.id in ROLE_WHITELIST for role in self.interaction.user.roles
        ):
            await self.interaction.response.send_message(
                content="You do not have permission to delete this!",
                ephemeral=True,
            )
            return

        preview = (
            f"**Map Code:** {map_document.code}\n"
            f"**Map Name:** {map_document.map_name}\n"
            f"**Creator(s):** {map_document.creator}\n"
            f"**Description:** {map_document.description}\n"
            f"**Map Types:** {', '.join(map_document.map_type)}\n"
        )

        view = MapSubmitView(confirm_disabled=False)
        view.remove_item(view.select_menu)

        await self.interaction.response.send_message(
            content=preview, ephemeral=True, view=view
        )

        await view.wait()
        if view.confirm.value:
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

        if self.interaction.user.id != map_document.user_id and not any(
            role.id in ROLE_WHITELIST for role in self.interaction.user.roles
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

        view = MapSubmitView(confirm_disabled=False)
        for x in view.select_menu.options:
            if x.label in map_document.map_type:
                x.default = True

        await self.interaction.response.send_message(
            content=preview, ephemeral=True, view=view
        )

        await view.wait()

        map_document.map_type = view.select_menu.values or map_document.map_type

        if view.confirm.value:
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


class RandomMap(discord.SlashCommand, guilds=[GUILD_ID], name="random_map"):
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
        embeds = split_embeds(embed, search, maps_embed_fields)

        view = Paginator(embeds, self.interaction.user, timeout=None)
        await self.interaction.response.send_message(
            embed=view.formatted_pages[0], view=view, ephemeral=True
        )
        await view.wait()
