from typing import Optional

from discord.ext import commands
from thefuzz import fuzz

from database.documents import Map
from utils.embed import create_embed
from utils.enum import MapNames, MapTypes
from logging import getLogger
from operator import itemgetter

from utils.maps import split_map_embeds
from views.paginator import Paginator

logger = getLogger(__name__)


class MapSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        slash_command=True, name="maps", slash_commands_guilds=[195387617972322306]
    )
    async def search_maps(
        self,
        ctx: commands.Context,
        map_name: Optional[str] = commands.Option(
            description="Name of a particular Overwatch map."
        ),
        map_type: Optional[str] = commands.Option(
            description="A specific type of map."
        ),
        creator: Optional[str] = commands.Option(
            description="Name of a specific creator."
        ),
    ):
        """Search for maps."""

        fuzzy_name, fuzzy_type = None, None
        if map_name:
            fuzzy_name = self.fuzzy_map_enum(map_name)
        if map_type:
            fuzzy_type = self.fuzzy_map_type_enum(map_type)

        search = await Map.filter_search(
            map_name=fuzzy_name,
            map_type=fuzzy_type,
            creator=creator,
        )

        embed = create_embed(title=f"Map Search", desc="", user=ctx.author)
        embeds = split_map_embeds(embed, search)

        view = Paginator(embeds, ctx.author, timeout=None)
        await ctx.send(embed=view.formatted_pages[0], view=view, ephemeral=True)

        await view.wait()

    @staticmethod
    def fuzzy_map_enum(map_name: str) -> MapNames:
        values = [
            (member, fuzz.partial_ratio(map_name, member.value))
            for name, member in MapNames.__members__.items()
        ]
        return max(values, key=itemgetter(1))[0]

    @staticmethod
    def fuzzy_map_type_enum(map_type: str) -> MapTypes:
        values = [
            (member, fuzz.partial_ratio(map_type, member.value))
            for name, member in MapTypes.__members__.items()
        ]
        return max(values, key=itemgetter(1))[0]


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapSearch(bot))
