import discord

from utils.constants import GUILD_ID


def setup(bot):
    bot.application_command(SubmitParent)
    bot.application_command(EditParent)
    bot.application_command(DeleteParent)


class SubmitParent(discord.SlashCommand, guilds=[GUILD_ID], name="submit"):
    """Submit slash command parent class."""


class EditParent(discord.SlashCommand, guilds=[GUILD_ID], name="edit"):
    """Edit slash command parent class."""


class DeleteParent(discord.SlashCommand, guilds=[GUILD_ID], name="delete"):
    """Delete slash command parent class."""
