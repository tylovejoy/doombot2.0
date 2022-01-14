import discord
from logging import getLogger
from utils.constants import GUILD_ID

logger = getLogger(__name__)


def setup(bot: discord.Client):
    logger.info("Loading ------------- PARENTS...")
    bot.application_command(SubmitParent)
    bot.application_command(EditParent)
    bot.application_command(DeleteParent)
    bot.application_command(TournamentParent)
    bot.application_command(CreateParent)
    bot.application_command(TournamentMissionsParent)


class CreateParent(discord.SlashCommand, guilds=[GUILD_ID], name="create"):
    """Create slash command parent class."""


class SubmitParent(discord.SlashCommand, guilds=[GUILD_ID], name="submit"):
    """Submit slash command parent class."""


class EditParent(discord.SlashCommand, guilds=[GUILD_ID], name="edit"):
    """Edit slash command parent class."""


class DeleteParent(discord.SlashCommand, guilds=[GUILD_ID], name="delete"):
    """Delete slash command parent class."""


class TournamentParent(discord.SlashCommand, guilds=[GUILD_ID], name="tournament"):
    """Tournament slash command parent class."""


class TournamentMissionsParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="missions"
):
    """Tournament missions slash command parent class."""


class TournamentSubmitParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="submit", parent=TournamentParent
):
    """Tournament slash command parent class."""
