import discord
from discord.ext import commands
from logging import getLogger

from database.documents import database_init

logger = getLogger(__name__)

DOOMBOT_ASCII = r"""
______  _____  _____ ___  _________  _____  _____
|  _  \|  _  ||  _  ||  \/  || ___ \|  _  ||_   _|
| | | || | | || | | || .  . || |_/ /| | | |  | |
| | | || | | || | | || |\/| || ___ \| | | |  | |
| |/ / \ \_/ /\ \_/ /| |  | || |_/ /\ \_/ /  | |
|___/   \___/  \___/ \_|  |_/\____/  \___/   \_/
"""


class DoomBot(commands.Bot):
    def __init__(self, **kwargs):
        """Initialize Bot."""
        intents = discord.Intents(
            guild_reactions=True,
            guild_messages=True,
            guilds=True,
            dm_reactions=True,
            dm_messages=True,
            webhooks=True,
            members=True,
            emojis=True,
        )
        super().__init__(
            command_prefix=commands.when_mentioned_or("/"),
            case_insensitive=True,
            description="", 
            intents=intents,
            slash_command_guilds=[195387617972322306]
        )

        
    

    async def on_ready(self):
        app_info = await self.application_info()
        logger.info(
            f"{DOOMBOT_ASCII}"
            f"\nLogged in as: {self.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {app_info.owner}\n"
        )
        await database_init()