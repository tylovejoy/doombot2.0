import logging
from os import environ

from doombot import DoomBot
from slash import maps, records, parents, tournament, exp, tags

logger = logging.getLogger()
logger.setLevel(logging.INFO)

consoleHandle = logging.StreamHandler()
consoleHandle.setLevel(logging.INFO)
consoleHandle.setFormatter(
    logging.Formatter("%(name)-18s :: %(levelname)-8s :: %(message)s")
)
logger.addHandler(consoleHandle)

# Discord setup

bot = DoomBot()


def load_all_extensions():
    """Load all slashes."""
    logger.info("Loading slash...")
    parents.setup(bot)
    maps.setup(bot)
    records.setup(bot)
    tournament.setup(bot)
    exp.setup(bot)
    tags.setup(bot)
    logger.info("Slash loaded.")


@bot.event
async def setup():
    """Upload slash commands to discord."""
    await bot.upload_guild_application_commands()


TOKEN = environ["TOKEN"]
# Load cogs before running the bot for slash commands to be registered
load_all_extensions()
bot.run(TOKEN)
