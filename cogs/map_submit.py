from typing import Optional
import discord
from discord.ext import commands
from logging import getLogger

logger = getLogger(__name__)


class MapSubmit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        slash_command=True, name="submitmap", slash_commands_guilds=[195387617972322306]
    )
    async def submit_maps(
        self,
        ctx: commands.Context,
        map_code: str = commands.Option(
            description="Workshop code for this parkour map."
        ),
        map_name: str = commands.Option(
            description="Name of a particular Overwatch map."
        ),
        creator: str = commands.Option(
            description="Creator(s) of the map."
        ),
        description: str = commands.Option(
            description="Description of the map."
        ),
    ):
        """Submit maps."""
        pass