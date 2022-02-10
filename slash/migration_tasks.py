import discord
from logging import getLogger

from database.documents import EXPRanks, ExperiencePoints
from utils.constants import GUILD_ID
from utils.utilities import logging_util

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "EXP"))
    bot.application_command()


all_ranks = {  #         TA MC HC BO
    593838073012289536: (3, 3, 3),  # Blynq
    343862912630259714: (3, 3, 2),  # Dralone
    637782279552368641: (3, 2, 1),  # Frosty
    603618693318049820: (2, 2, 3),  # Frost
    294502010445758464: (2, 3, 3),  # Geshem
    147164404591493120: (3, 1, 1),  # Law
    360821403127119872: (3, 3, 3),  # Onzi
    462305088124354560: (3, 3, 3),  # Tamar
    525448201495379969: (3, 3, 2),  # Sproul
    187340057462439951: (3, 3, 0),  # Neo
    297831804642000916: (2, 2, 3),  # CmoiFlo
    386099475573374978: (2, 2, 2),  # (A)bandnd
    338375078205194240: (1, 2, 2),  # bchorn
    300896613436751873: (2, 2, 0),  # converge
    235471338536435713: (2, 2, 0),  # Evvo
    248892037804457984: (2, 2, 0),  # Yoshi
    244507811583623170: (2, 2, 2),  # Mocking
    871090022391087164: (0, 0, 2),  # Doomsweat
    836288029924524063: (2, 1, 1),  # Le Monke
    538692112305356801: (2, 2, 1),  # Lehuga
    574804014399750164: (2, 2, 2),  # Taizy
    146244622870380544: (0, 2, 0),  # Mercurial
    558361127126564894: (1, 1, 1),  # EmeraldPotato
    685107786820092024: (2, 2, 2),  # Tosal
    664483930816249878: (1, 0, 2),  # LoopeR
    141372217677053952: (1, 2, 1),  # nebula
    306809785129369602: (2, 2, 1),  # nevercane
    326983993180291073: (2, 0, 0),  # Odalv
    659430881114456064: (1, 0, 0),  # Dragonweeber
    544161037176406018: (2, 0, 0),  # Sharti/Teque
    787729170108776469: (1, 2, 1),  # Timetwister
    505754200354062336: (2, 0, 0),  # Silentsword/zxzyw
    726369887143985182: (1, 1, 1),  # Chaewon
    690576696037867571: (1, 0, 0),  # Namelessboi
    584469072171761666: (1, 0, 0),  # Chienspecteur
    422712500199358475: (1, 0, 0),  # TheDarkBoy
    543720258112978947: (1, 1, 0),  # Shadow_
    696014144964395069: (1, 1, 1),  # Viney
    307287887873835020: (1, 0, 0),  # superior chad/kirbey griffin
    571717879419109417: (),  # Legolas
    140259458348482560: (),  # Alayy
}

rank_convert = {
    0: "Unranked",
    1: "Gold",
    2: "Diamond",
    3: "Grandmaster",
}


class MigrationTasks(discord.SlashCommand, guilds=[GUILD_ID], name="migrate"):
    """Migrate to doombot2.0"""

    async def callback(self) -> None:
        logger.info(logging_util("Migration", "BEGIN EXP TRANSFER"))
        members = self.interaction.guild.members
        member_list = []
        mee6_xp = {
            "nebula": 127090,
            # TODO: This needs to be an actual dict from mee6_xp file
        }
        for member in members:
            xp = 0
            if member.name in mee6_xp.keys():
                xp = mee6_xp[member.name]

            rank = EXPRanks()
            if member.id in all_ranks.keys():
                rank.ta = rank_convert[all_ranks[member.id][0]]
                rank.mc = rank_convert[all_ranks[member.id][1]]
                rank.hc = rank_convert[all_ranks[member.id][2]]
                rank.bo = "Unranked"

            member_list.append(
                ExperiencePoints(
                    user_id=member.id,
                    alias=member.name,
                    alerts_enabled=True,
                    xp=xp,
                    rank=rank,
                )
            )
        await ExperiencePoints.insert_many(member_list)
