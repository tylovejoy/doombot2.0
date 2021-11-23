from typing import NoReturn, Optional, Union
import discord
from discord.ext import commands
from thefuzz import fuzz
from thefuzz import process
from src.database.documents import Map
from utils.enum import MapNames
from logging import getLogger
from operator import itemgetter

logger = getLogger(__name__)

class MapSearch(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        slash_command=True
    )
    async def search(
        self, 
        ctx: commands.Context,
        map_name: str = commands.Option(description="Name of a particular Overwatch map.")
    ):
        """Search for maps."""
        fuzzy_name = self.get_map_name(map_name)
        await ctx.send(f"Here are all the Doomfist Parkour maps for {fuzzy_name}", ephemeral=True)

    @staticmethod
    def get_map_name(map_name):
        values = [(member, fuzz.partial_ratio(map_name, str(member))) for name, member in MapNames.__members__.items()]
        return max(values, key=itemgetter(1))[0]
        
    


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapSearch(bot))