import datetime
from logging import getLogger
from typing import Literal

import dateparser
import discord

from database.documents import Events
from slash.parents import CreateParent
from slash.slash_command import Slash
from utils.constants import GAME_ROLE, GUILD_ID, MOVIE_ROLE, SERVER_ANNOUNCEMENTS
from utils.utilities import check_permissions, logging_util

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "TOURNAMENT"))
    bot.application_command(CreateEvent)
    bot.application_command(EndEvent)


class EndEvent(
    Slash,
    guilds=[GUILD_ID],
    name="end-event",
):
    """End event."""

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)

        event = await Events.find_one(Events.started == True)
        guild = self.client.get_guild(self.interaction.guild_id)
        await guild.get_channel(event.text).delete()
        await guild.get_channel(event.voice).delete()
        await guild.get_channel(event.category).delete()
        await event.delete()


class CreateEvent(Slash, guilds=[GUILD_ID], name="event", parent=CreateParent):
    """Create an event."""

    event_type: Literal["Movie", "Game"] = discord.Option(
        description="What type of event is it?",
    )

    schedule_start: str = discord.Option(
        description="When should the event start?",
    )

    details: str = discord.Option(
        description="Details of the event such as movie or game title."
    )

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        await check_permissions(self.interaction)

        self.schedule_start: datetime.datetime = dateparser.parse(
            self.schedule_start,
            settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": True},
        )

        schedule_end = self.schedule_start + datetime.timedelta(hours=2)

        iso_start = self.schedule_start.isoformat()
        iso_end = schedule_end.isoformat()

        event_data = await self.client.http.create_guild_scheduled_event(
            GUILD_ID,
            channel_id=None,
            name=f"{self.event_type} Night!",
            description=self.details,
            scheduled_start_time=iso_start,
            scheduled_end_time=iso_end,
            entity_type=3,
            privacy_level=2,
            entity_metadata={"location": "Event Channels"},
        )
        document = Events(
            event_id=event_data["id"],
            event_name=self.event_type + " Night!",
            schedule_start=self.schedule_start,
            started=False,
        )
        await document.save()

        guild = self.client.get_guild(GUILD_ID)
        announcements_channel = guild.get_channel(SERVER_ANNOUNCEMENTS)

        if self.event_type == "Movie":
            role = guild.get_role(MOVIE_ROLE)
        elif self.event_type == "Game":
            role = guild.get_role(GAME_ROLE)

        await announcements_channel.send(
            f"{role.mention}\n"
            f"{self.event_type} Night!\n"
            "Check the event link for more info.\n"
            f"https://discord.com/events/{event_data['guild_id']}/{event_data['id']}"
        )
