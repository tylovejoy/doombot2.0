from logging import getLogger

import discord

from utils.constants import GUILD_ID
from utils.utilities import logging_util

logger = getLogger(__name__)


def setup(bot: discord.Client):
    logger.info(logging_util("Loading", "PARENTS"))
    bot.application_command(SubmitParent)
    bot.application_command(EditParent)
    bot.application_command(DeleteParent)
    bot.application_command(TournamentParent)
    bot.application_command(CreateParent)
    bot.application_command(TournamentMissionsParent)
    bot.application_command(TournamentOrgParent)
    bot.application_command(ModParent)


class CreateParent(discord.SlashCommand, guilds=[GUILD_ID], name="create"):
    """Create slash command parent class."""


class ModParent(discord.SlashCommand, guilds=[GUILD_ID], name="mod"):
    """Create slash command parent class."""

class SubmitParent(discord.SlashCommand, guilds=[GUILD_ID], name="submit"):
    """Submit slash command parent class."""


class EditParent(discord.SlashCommand, guilds=[GUILD_ID], name="edit"):
    """Edit slash command parent class."""


class DeleteParent(discord.SlashCommand, guilds=[GUILD_ID], name="delete"):
    """Delete slash command parent class."""


class TournamentParent(discord.SlashCommand, name="tournament"):
    """Tournament slash command parent class."""


class TournamentMissionsParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="missions"
):
    """Tournament missions slash command parent class."""


class TournamentOrgParent(discord.SlashCommand, guilds=[GUILD_ID], name="org"):
    """Tournament org only commands parent class."""


# class TournamentSubmitParent(
#     discord.SlashCommand, guilds=[GUILD_ID], name="submit", parent=TournamentParent
# ):
#     """Tournament slash command parent class."""
