import logging
from os import environ

from database.documents import database_init
from doombot import DoomBot
from slash import (
    events,
    exp,
    guides,
    maps,
    parents,
    records,
    tags,
    tournament,
    store,
    migration_tasks,
    mods,
)
from utils.utilities import logging_util

logger = logging.getLogger()
logger.setLevel(logging.INFO)

consoleHandle = logging.StreamHandler()
consoleHandle.setLevel(logging.INFO)
consoleHandle.setFormatter(
    logging.Formatter("%(name)-18s :: %(levelname)-8s :: %(message)s")
)
logger.addHandler(consoleHandle)

bot = DoomBot()


def load_all_extensions():
    """Load all slashes."""
    logger.info(logging_util("Loading", "SLASH COMMANDS"))
    parents.setup(bot)
    maps.setup(bot)
    records.setup(bot)
    tournament.setup(bot)
    exp.setup(bot)
    tags.setup(bot)
    guides.setup(bot)
    events.setup(bot)
    mods.setup(bot)
    # store.setup(bot)
    logger.info(logging_util("Loading Complete", "SLASH COMMANDS"))


@bot.event
async def setup():
    """Upload slash commands to discord."""

    await database_init()
    logger.info(logging_util("Uploading", "SLASH COMMANDS"))
    await bot.upload_guild_application_commands()
    await bot.upload_global_application_commands()
    logger.info(logging_util("Uploading Complete", "SLASH COMMANDS"))


TOKEN = environ["TOKEN"]
# Load cogs before running the bot for slash commands to be registered
load_all_extensions()
bot.run(TOKEN)
