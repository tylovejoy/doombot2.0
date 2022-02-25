from logging import getLogger
from typing import Optional

import aiohttp
import discord

from database.documents import Tags
from utils.errors import SearchNotFound
from slash.parents import CreateParent, DeleteParent
from slash.slash_command import Slash
from utils.constants import GUILD_ID
from utils.embed import create_embed
from utils.utilities import (
    case_ignore_compare,
    check_permissions,
    logging_util,
)
from views.basic import ConfirmView

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "TAGS"))
    bot.application_command(TagsCommand)
    bot.application_command(WorkshopHelp)


async def _autocomplete(options, focused, list_obj):
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


class DeleteTag(
    Slash, guilds=[GUILD_ID], name="tag", parent=DeleteParent
):
    """Delete a tag."""

    name: str = discord.Option(
        description="Which tag should be deleted?", autocomplete=True
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)

        tag = await Tags.find_one(Tags.name == self.name)

        if not tag:
            raise SearchNotFound("Tag does not exist.")
        
        view = ConfirmView()
        if await view.start(
            self.interaction,
            f"**{tag.name}**\n\n{tag.content}\n\nDo you want to create this tag?",
            f"**{tag.name}** has been deleted.",
        ):
            await tag.delete()

    async def autocomplete(self, options, focused):
        tag_names = await Tags.find_all_tag_names()
        return await _autocomplete(options, focused, tag_names)


class CreateTag(
    discord.SlashCommand, guilds=[GUILD_ID], name="tag", parent=CreateParent
):
    """Create a tag."""

    name: str = discord.Option(description="What should the tag be called?")
    content: str = discord.Option(description="What should the content of the tag be?")

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)
        
        
        tag = Tags(name=self.name, content=self.content)
        if not Tags.exists(self.name):
            raise SearchNotFound(
                f"**{tag.name}** already exists! This tag was not created."
            )

        view = ConfirmView()

        if await view.start(
            self.interaction,
            f"**{tag.name}**\n\n{tag.content}\n\nDo you want to create this tag?",
            f"**{tag.name}** has been added as a new tag.",
        ):
            await tag.save()


class TagsCommand(discord.SlashCommand, name="tag"):
    """Display answers for commonly asked questions."""

    name: str = discord.Option(description="Which tag to display?", autocomplete=True)

    async def callback(self) -> None:
        await self.defer()
        tag = await Tags.find_one(Tags.name == self.name)
        await self.interaction.edit_original_message(
            content=f"**{tag.name}**\n\n{tag.content}"
        )

    async def autocomplete(self, options, focused):
        tag_names = await Tags.find_all_tag_names()
        return await _autocomplete(options, focused, tag_names)


class WorkshopHelp(discord.SlashCommand, name="workshop"):
    """Display Overwatch Workshop information."""

    search: str = discord.Option(description="What to search?", autocomplete=True)
    hidden: Optional[bool] = discord.Option(
        "Should this be visible to everyone? Default: True.", default=True
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=self.hidden)
        self.search = self.search.replace(" ", "-")
        url = f"https://workshop.codes/wiki/search/{self.search}.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = list(await resp.json())[0]
                embed = create_embed(
                    data.get("title"),
                    data.get("content"),
                    self.interaction.user,
                )

                await self.interaction.edit_original_message(embed=embed)

    async def autocomplete(self, options, focused):
        return await _autocomplete(options, focused, self.client.ws_list)
