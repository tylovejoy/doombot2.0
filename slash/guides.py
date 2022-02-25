from logging import getLogger
from typing import Dict, Union

import discord

from database.documents import Guide
from errors import DocumentAlreadyExists, SearchNotFound
from slash.parents import DeleteParent, SubmitParent
from slash.slash_command import RecordSlash
from utils.constants import GUILD_ID
from utils.utilities import logging_util, preprocess_map_code
from views.basic import ConfirmView, GuideDeleteView
from views.paginator import Paginator

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "TOURNAMENT"))
    bot.application_command(ViewGuide)


class DeleteGuide(
    RecordSlash,
    guilds=[GUILD_ID],
    name="guide",
    parent=DeleteParent,
):

    map_code: str = discord.Option(
        description="Workshop code for the specific map.",
        autocomplete=True,
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        search = await Guide.find_one(Guide.code == self.map_code)
        guides = [
            guide
            for guide, owner in zip(search.guide, search.guide_owner)
            if owner == self.interaction.user.id
        ]
        view = GuideDeleteView(guides)
        await self.send(content="Which guide do you want to delete?", view=view)
        await view.wait()

        if not view.confirm.value:
            return

        chosen_index = search.guide.index(view.dropdown.values[0])
        search.guide.pop(chosen_index)
        search.guide_owner.pop(chosen_index)
        await search.save()


class ViewGuide(
    RecordSlash,
    name="guide",
):
    map_code: str = discord.Option(
        description="Workshop code for the specific map.",
        autocomplete=True,
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        search = await Guide.find_one(Guide.code == self.map_code)

        if not search:
            raise SearchNotFound(f"There are no guides for {self.map_code} yet.")

        links = [link for link in search.guide]
        view = Paginator(links, self.interaction.user)
        await view.start(self.interaction)


class SubmitGuide(
    RecordSlash,
    guilds=[GUILD_ID],
    name="guide",
    parent=SubmitParent,
):
    map_code: str = discord.Option(
        description="Workshop code for the specific map.",
        autocomplete=True,
    )
    link: str = discord.Option(
        description="Link to guide.",
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        self.map_code = preprocess_map_code(self.map_code)
        search = await Guide.find_one(Guide.code == self.map_code)

        if search:
            if any([link for link in search.guide if link == self.link]):
                raise DocumentAlreadyExists("This particular link has already been added.")
        else:
            search = Guide(code=self.map_code)

        search.guide.append(self.link)
        search.guide_owner.append(self.interaction.user.id)

        view = ConfirmView()
        if await view.start(
            self.interaction,
            f"Code: {self.map_code}\n" f"URL: {self.link}\n\n" "Is this correct?",
            "Added.",
        ):
            await search.save()
