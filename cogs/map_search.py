from discord.ext import commands
from thefuzz import fuzz

from database.documents import Map
from utils.embed import create_embed
from utils.enum import MapNames
from logging import getLogger
from operator import itemgetter

from utils.maps import split_map_embeds

logger = getLogger(__name__)


class MapSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(slash_command=True, name="search")
    async def search(
        self,
        ctx: commands.Context,
        map_name: str = commands.Option(
            description="Name of a particular Overwatch map."
        ),
    ):
        """Search for maps."""
        await ctx.trigger_typing()
        fuzzy_name = self.get_map_name(map_name)
        list_of_maps = await Map.get_all_maps(fuzzy_name)

        embed = create_embed(title=f"{fuzzy_name} maps", desc="", user=ctx.author)

        embeds = split_map_embeds(embed, list_of_maps)

        await ctx.send(
            f"Here are all the Doomfist Parkour maps for {fuzzy_name}",
            embeds=embeds,
            ephemeral=True,
        )

    @staticmethod
    def get_map_name(map_name):
        values = [
            (member, fuzz.partial_ratio(map_name, str(member)))
            for name, member in MapNames.__members__.items()
        ]
        return max(values, key=itemgetter(1))[0]


def setup(bot):
    """Add Cog to Discord bot."""
    bot.add_cog(MapSearch(bot))
