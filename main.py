import argparse
from os import environ
import logging
from slash import map_commands
from doombot import DoomBot

# Arguments
parser = argparse.ArgumentParser(description="Choose a logging level.")
parser.add_argument(
    "--log",
    nargs="?",
)
args = parser.parse_args()

# Logging setup
logging_level = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
}

logger = logging.getLogger()
logger.setLevel(logging_level.get(args.log, logging.INFO))

consoleHandle = logging.StreamHandler()
consoleHandle.setLevel(logging_level.get(args.log, logging.INFO))
consoleHandle.setFormatter(
    logging.Formatter("%(name)-18s :: %(levelname)-8s :: %(message)s")
)
logger.addHandler(consoleHandle)

# Discord setup

bot = DoomBot()


def load_all_extensions():
    """Load all slashes."""
    logger.info("Loading slash...")
    map_commands.setup(bot)
    logger.info("Slash loaded.")


@bot.event
async def setup():
    await bot.upload_guild_application_commands()


TOKEN = environ["TOKEN"]
# Load cogs before running the bot for slash commands to be registered
load_all_extensions()
bot.run(TOKEN)
