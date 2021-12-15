import discord

from utils.constants import GUILD_ID


def setup(bot):
    bot.application_command(SubmitParent)
    bot.application_command(EditParent)
    bot.application_command(DeleteParent)
    bot.application_command(TournamentParent)
    bot.application_command(TournamentSubmitParent)


class SubmitParent(discord.SlashCommand, guilds=[GUILD_ID], name="submit"):

    """Submit slash command parent class."""


class EditParent(discord.SlashCommand, guilds=[GUILD_ID], name="edit"):

    """Edit slash command parent class."""


class DeleteParent(discord.SlashCommand, guilds=[GUILD_ID], name="delete"):

    """Delete slash command parent class."""


class TournamentParent(discord.SlashCommand, guilds=[GUILD_ID], name="tournament"):

    """Tournament slash command parent class."""


class TournamentSubmitParent(
    discord.SlashCommand, guilds=[GUILD_ID], name="tournament", parent=SubmitParent
):

    """Tournament slash command parent class."""
