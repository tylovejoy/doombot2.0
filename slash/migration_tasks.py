from logging import getLogger

import discord

from database.documents import ExperiencePoints, EXPRanks
from utils.constants import GUILD_ID
from utils.utilities import check_permissions, logging_util

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "MIGRATION"))
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
    571717879419109417: (2, 3, 2),  # Legolas
    140259458348482560: (1, 0, 0),  # Alayy
}

rank_convert = {
    0: "Unranked",
    1: "Gold",
    2: "Diamond",
    3: "Grandmaster",
}
# TODO: This needs to be updated.
mee6_xp = {
    "Blynq": 299900,
    "TaMaR": 172400,
    "Dralone": 158200,
    "onzi": 156700,
    "frosty": 147300,
    '$+;$(?¥*=°€°π°¢™£¥®™✓©°°€¶~©%+"': 111200,
    "Born Magical": 106700,
    "Law": 98200,
    "Geshem8": 73000,
    "L.": 55800,
    "CmoiFlo": 40200,
    "timetwister": 38600,
    "nevercane": 33000,
    "ʟᴇ ᴍᴏɴᴋᴇ": 32299,
    "opare": 31500,
    "exylophone": 25200,
    "chaewon": 20600,
    "(A)Bandnd": 19300,
    "nebula": 19200,
    "boo": 18200,
    "slasso": 17800,
    "spork": 16900,
    "FiLipos": 16500,
    "Evvo": 15300,
    "Doomsweat": 14000,
    "frost": 12800,
    "Tosal": 12000,
    "EmeraldPotato": 11800,
    "Secozzi": 11400,
    "Shadow_": 10000,
    "Crunchy": 9800,
    "pro midget punter": 8500,
    "Ce3": 7700,
    "zxzyw": 7300,
    "LoopeR": 7100,
    "Alayy": 6400,
    "wish": 6400,
    "cod fish": 6300,
    "Falafel": 6300,
    "FrostyFeet": 5900,
    "Wolfe": 5900,
    "AoĐ": 5000,
    "DiaZ": 4400,
    "P03": 4200,
    "dragonweeber4538": 4200,
    "Converge": 4000,
    "Chienspecteur": 4000,
    ".y": 3800,
    "kirby griffin": 3500,
    "Lke": 3300,
    "-MiKO--": 3300,
    "namelessboi": 3200,
    "Shiden": 3100,
    "Sharti72": 2800,
    "Doodles": 2800,
    "eren yeager": 2800,
    "jjojehongg": 2600,
    "mr.tree": 2500,
    "viney": 2200,
    "tron": 2100,
    "bad girl": 1900,
    "N00B_bvt_Pro": 1900,
    "taizy": 1900,
    "Talyir": 1800,
    "Hhanuska": 1600,
    "WhoAreYou": 1300,
    "Dolchio": 1100,
    "andres": 1100,
    "Cheezie": 1000,
    "Odalv": 895,
    "FishoFire": 791,
    "Asdfs402": 588,
    "taki": 500,
    "Luen": 500,
    "Sniper": 500,
    "Kruczon": 489,
    "[)(]": 417,
    "Peralax": 329,
    "Kenai": 298,
    "OmarT": 250,
    "JetSetRadio": 238,
    "Enrath": 221,
    "Rax": 211,
    "khandescension": 190,
    "Hax": 177,
    "zeboNik": 152,
    "(3": 149,
    "Mersain": 58,
    "Nachos": 142,
    "bokoli": 133,
    "N3o": 130,
    "Feloniousbolus": 124,
    "thecyberon": 120,
    "wegorz": 112,
    "nsbunited": 107,
    "Benny": 100,
    "hellhammer": 100,
    "GameIt": 94,
    "QUOTIENT": 82,
    "Tundra": 71,
    "ImBlueBunny": 67,
    "STR": 58,
    "ZzackK": 54,
    "EvilzShadow": 53,
    "lornafex": 50,
    "TheDarkBoy": 43,
    "Arctic": 42,
    "dissapointment": 42,
    "SirVitek": 40,
    "фкккееенннгггзззммm": 36,
    "Cheddi": 33,
    "Carymel": 32,
    "purplehearts": 32,
    "Lilyboi": 30,
    "Arion_Wang": 27,
    "ReusableTpot": 27,
    "Articular": 26,
    "Pouyou": 26,
    "Rajeem": 22,
    "Pastel Princess": 22,
    "SunnyApple": 22,
    "ᐯㄖ尺卩卂ㄥ": 20,
    "Juzam": 19,
    "XD": 19,
    "gachiHYPER": 19,
    "Ruin": 18,
    "Noara95": 18,
    "Shîzukuu": 16,
    "MasonG": 16,
    "DBX_5": 15,
    "Phixel": 14,
    "펜실pensil": 14,
    "Пуська": 14,
    "-------": 13,
    "aphrodite": 13,
    "PLun": 12,
    "Zawsze": 12,
    "Butterfly": 11,
    "Amer": 10,
    "Elroxx": 10,
    "Wafan": 9,
    "ᴍᴏʜᴀɴɴᴇᴅ": 9,
    "Danilo": 9,
    "BartmastA": 9,
    "Clément": 9,
    "macintof": 8,
    "SpecsG": 8,
    "Ayana": 8,
    "zuhxxy wuhxxy": 6,
    "nez": 6,
    "Mercanzi": 5,
    "Eon": 5,
    "oops": 5,
    "hoga": 5,
    "FordDriver5000": 4,
    "DarkShark": 4,
    "Rookie": 4,
    "Nekroido": 3,
    "korn": 3,
    "ItsZoid": 3,
    "Dasani Water": 3,
}


class MigrationTasks(discord.SlashCommand, guilds=[GUILD_ID], name="migrate"):
    """Migrate to doombot2.0"""

    async def callback(self) -> None:
        await self.defer(ephemeral=True)
        if not await check_permissions(self.interaction):
            return
        logger.info(logging_util("Migration", "BEGIN EXP TRANSFER"))
        members = self.interaction.guild.members
        member_list = []

        for member in members:
            xp = 0
            if member.name in mee6_xp.keys():
                xp = mee6_xp[member.name]

            rank = EXPRanks()
            if member.id in all_ranks.keys():
                rank.ta = rank_convert[all_ranks[member.id][0]]
                rank.mc = rank_convert[all_ranks[member.id][1]]
                rank.hc = rank_convert[all_ranks[member.id][2]]
                rank.bo = "Grandmaster"

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
        await self.interaction.edit_original_message(content="Done.")
