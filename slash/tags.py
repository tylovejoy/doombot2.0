from logging import getLogger
from typing import Optional
import aiohttp
import discord
from discord.app import AutoCompleteResponse

from database.documents import Tags
from utils.utilities import case_ignore_compare
from utils.constants import GUILD_ID
from utils.embed import create_embed

logger = getLogger(__name__)


def setup(bot):
    bot.application_command(TagsCommand)
    bot.application_command(WorkshopHelp)


async def _autocomplete(options, focused, list_obj):
    if options[focused] == "":
        return AutoCompleteResponse({k: k for k in list_obj[:25]})

    if focused == "name":
        count = 0
        autocomplete_ = {}
        for k in list_obj:
            if case_ignore_compare(k, options[focused]) and count < 25:
                autocomplete_[k] = k
                count += 1

        return AutoCompleteResponse(autocomplete_)


class TagsCommand(discord.SlashCommand, guilds=[GUILD_ID], name="tag"):
    """Display answers for commonly asked questions."""

    name: str = discord.Option(description="Which tag to display?", autocomplete=True)

    async def callback(self) -> None:
        tag = await Tags.find_one(Tags.name == self.name)
        formatted_string = f"**{tag.name}**\n\n{tag.content}"
        await self.interaction.response.send_message(formatted_string)

    async def autocomplete(self, options, focused):
        tag_names = await Tags.find_all_tag_names()
        return await _autocomplete(options, focused, tag_names)


class WorkshopHelp(discord.SlashCommand, guilds=[GUILD_ID], name="workshop"):
    """Display Overwatch Workshop information."""

    search: str = discord.Option(description="What to search?", autocomplete=True)
    hidden: Optional[bool] = discord.Option(
        "Should this be visible to everyone? Default: True.", default=True
    )

    async def callback(self) -> None:
        self.search = self.search.replace(" ", "-")
        async with aiohttp.ClientSession() as session:

            url = f"https://workshop.codes/wiki/search/{self.search}.json"
            async with session.get(url) as resp:
                data = list(await resp.json())[0]
                embed = create_embed(
                    data.get("title"),
                    data.get("content"),
                    self.interaction.user,
                )

                await self.interaction.response.send_message(
                    embed=embed, ephemeral=self.hidden
                )

    async def autocomplete(self, options, focused):
        return await _autocomplete(options, focused, self.client.ws_list)
