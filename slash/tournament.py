import discord

from slash.parents import SubmitParent
from utils.constants import GUILD_ID


def setup(bot):
    bot.application_command(TournamentParent)
    bot.application_command(Hardcore)


class TournamentParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="tournament", parent=SubmitParent
):

    """Tournament slash command parent class."""


class Hardcore(
    discord.SlashCommand, guilds=[GUILD_ID], name="hardcore", parent=TournamentParent
):

    """Hardcore tournament submission."""
