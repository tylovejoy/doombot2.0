from datetime import datetime
import discord
from database.documents import Tournament, TournamentCategories, TournamentMaps

from slash.parents import SubmitParent
from utils.constants import GUILD_ID


def setup(bot):
    bot.application_command(TournamentParent)
    bot.application_command(TournamentSubmitParent)
    bot.application_command(Hardcore)


class TournamentParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="tournament"
):

    """Tournament slash command parent class."""

    async def callback(self) -> None:
        """Callback for submitting records slash command."""
        maps = TournamentCategories(
            ta=TournamentMaps(code="code1", creator="creator", map_name="Hanamura"),
            mc=TournamentMaps(code="code2", creator="creator", map_name="Hanamura"),
            hc=TournamentMaps(code="code3", creator="creator", map_name="Hanamura"),
            bo=TournamentMaps(code="code4", creator="creator", map_name="Hanamura"),
        )
        
        tournament_document = Tournament(
            tournament_id=0,
            name="Tournament Test",
            active=True,
            bracket=False,
            schedule_start=datetime(1, 1, 1),
            schedule_end=datetime(1, 2, 1),
            maps=maps,
            records=TournamentCategories(),
            missions=TournamentCategories(),
        )

        await tournament_document.insert()
        await self.interaction.response.send_message("BING BONG", ephemeral=True)


class TournamentStart(
    discord.SlashCommand, guilds=GUILD_ID, name="start"
):

    """Create and start a new tournament."""



class TournamentSubmitParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="tournament", parent=SubmitParent
):

    """Tournament slash command parent class."""


class Hardcore(
    discord.SlashCommand, guilds=[GUILD_ID], name="hardcore", parent=TournamentSubmitParent
):

    """Hardcore tournament submission."""

    record: str = discord.Option(
        description="Your personal record. Format: HH:MM:SS.ss - You can omit the hours or minutes if they are 0."
    )