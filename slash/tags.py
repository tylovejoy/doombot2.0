from logging import getLogger
from typing import Optional
import aiohttp
import discord
from discord.app import AutoCompleteResponse
from utils.utilities import case_ignore_compare
from utils.constants import GUILD_ID
from utils.embed import create_embed
logger = getLogger(__name__)


def setup(bot):
    bot.application_command(Tags)
    bot.application_command(WorkshopHelp)


class Tags(discord.SlashCommand, guilds=[GUILD_ID], name="tag"):
    """Display answers for commonly asked questions."""

    name: str = discord.Option(
        description="Which tag to display?"
    )

    async def callback(self) -> None:
        pass


class WorkshopHelp(discord.SlashCommand, guilds=[GUILD_ID], name="workshop"):
    """Display answers for commonly asked questions."""

    search: str = discord.Option(
        description="What to search?",
        autocomplete=True
    )
    hidden: Optional[bool] = discord.Option(
        "Should this be visible to everyone? Default: True.",
        default=True
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

                await self.interaction.response.send_message(embed=embed, ephemeral=self.hidden)
    
    async def autocomplete(self, options, focused):
        if focused == "search":
            return AutoCompleteResponse(
                {
                    k: k
                    for k in self.client.ws_list[:25]
                    if case_ignore_compare(k, options[focused])
                }
            )
 
