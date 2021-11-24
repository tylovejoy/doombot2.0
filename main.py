import argparse
from pathlib import Path
from os import environ
import logging

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
logger.setLevel(logging_level[args.log])

consoleHandle = logging.StreamHandler()
consoleHandle.setLevel(logging_level[args.log])
consoleHandle.setFormatter(
    logging.Formatter("%(name)-18s :: %(levelname)-8s :: %(message)s")
)
logger.addHandler(consoleHandle)

# Discord setup

bot = DoomBot()


def load_all_extensions():
    """Load all *.py files in /cogs/ as Cogs."""

    cogs = [x.stem for x in Path("cogs").glob("*.py")]
    logger.info("Loading extensions...")
    for extension in cogs:
        try:
            bot.load_extension(f"cogs.{extension}")
            logger.info(f"Loading {extension}...")
        except Exception as e:
            error = f"{extension}\n {type(e).__name__} : {e}"
            logger.info(f"failed to load extension {error}")
    logger.info("Extensions loaded.")


TOKEN = environ["TOKEN"]
# Load cogs before running the bot for slash commands to be registered
load_all_extensions()
bot.run(TOKEN)
