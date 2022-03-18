from logging import getLogger
from typing import Optional
from unicodedata import category

import aiohttp
import discord

from database.documents import Tags
from slash.parents import CreateParent, DeleteParent
from slash.slash_command import TagSlash, WorkshopSlash
from utils.constants import GUILD_ID
from utils.embed import create_embed
from utils.errors import SearchNotFound
from utils.utilities import check_permissions, logging_util
from views.basic import ConfirmView

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "TAGS"))
    bot.application_command(TagsCommand)
    bot.application_command(WorkshopHelp)


class DeleteTag(TagSlash, guilds=[GUILD_ID], name="tag", parent=DeleteParent):
    """Delete a tag."""

    category: str = discord.Option(description="Which category?", autocomplete=True)
    name: str = discord.Option(
        description="Which tag should be deleted?", autocomplete=True
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)

        tag = await Tags.find_one(
            Tags.name == self.name, Tags.category == self.category
        )

        if not tag:
            raise SearchNotFound("Tag does not exist.")

        view = ConfirmView()
        if await view.start(
            self.interaction,
            f"**{tag.name}**\n\n{tag.content}\n\nDo you want to create this tag?",
            f"**{tag.name}** has been deleted.",
        ):
            await tag.delete()


class CreateTag(TagSlash, guilds=[GUILD_ID], name="tag", parent=CreateParent):
    """Create a tag."""

    category: str = discord.Option(
        description="What should the category be?", autocomplete=True
    )
    name: str = discord.Option(description="What should the tag be called?")
    content: str = discord.Option(description="What should the content of the tag be?")

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)

        if await Tags.exists(self.name, self.category):
            raise SearchNotFound(
                f"**{self.name}** already exists! This tag was not created."
            )

        tag = Tags(name=self.name, content=self.content, category=self.category)

        view = ConfirmView()

        if await view.start(
            self.interaction,
            f"**{tag.name}**\n\n{tag.content}\n\nDo you want to create this tag?",
            f"**{tag.name}** has been added as a new tag.",
        ):
            await tag.save()


class TagsCommand(TagSlash, name="tag"):
    """Display answers for commonly asked questions."""

    category: str = discord.Option(description="Which tag category?", autocomplete=True)
    name: str = discord.Option(description="Which tag to display?", autocomplete=True)

    async def callback(self) -> None:
        await self.defer()
        tag = await Tags.find_one(
            Tags.name == self.name, Tags.category == self.category
        )
        content = tag.content.replace(r"\\n", "\n")
        await self.interaction.edit_original_message(
            content=f"**{tag.name}**\n\n{content}"
        )


class WorkshopHelp(WorkshopSlash, name="workshop"):
    """Display Overwatch Workshop information."""

    search: str = discord.Option(description="What to search?", autocomplete=True)
    hidden: Optional[bool] = discord.Option(
        "Should this be visible to everyone? Default: True.", default=True
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=self.hidden)
        self.search = self.search.replace(" ", "-")
        url = f"https://workshop.codes/wiki/search/{self.search}.json"
        async with self.client.session.get(url) as resp:
            data = list(await resp.json())[0]
            embed = create_embed(
                data.get("title"),
                data.get("content"),
                self.interaction.user,
            )

            await self.interaction.edit_original_message(embed=embed)
