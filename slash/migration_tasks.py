from logging import getLogger

import discord

from database.documents import ExperiencePoints, EXPRanks
from utils.constants import GUILD_ID
from utils.utilities import check_permissions, logging_util

logger = getLogger(__name__)


def setup(bot):
    logger.info(logging_util("Loading", "MIGRATION"))
    bot.application_command(MigrationTasks)


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
    "Blynq": 346100,
    "TaMaR": 183200,
    "onzi": 171900,
    "frosty": 168700,
    "Dralone": 165400,
    '$+;$(?¥*=°€°π°¢™£¥®™✓©°°€¶~©%+"': 132800,
    "Born Magical": 125600,
    "Law": 98800,
    "Geshem8": 73000,
    "L.": 67700,
    "nevercane": 54000,
    "CmoiFlo": 40200,
    "timetwister": 38600,
    "Evvo": 35500,
    "ʟᴇ ᴍᴏɴᴋᴇ": 32299,
    "opare": 31500,
    "exylophone": 25200,
    "nebula": 22200,
    "slasso": 22100,
    "Doomsweat": 21000,
    "chaewon": 20600,
    "(A)Bandnd": 20400,
    "boo": 18200,
    "spork": 16900,
    "FiLipos": 16500,
    "Secozzi": 14300,
    "ThomasGengar": 14200,
    "Shadow_": 14000,
    "frost": 12800,
    "Tosal": 12000,
    "EmeraldPotato": 11800,
    "dragonweeber4538": 11600,
    "Crunchy": 9800,
    "Converge": 8700,
    "pro midget punter": 8500,
    "namelessboi": 8400,
    "Ce3": 7700,
    "zxzyw": 7300,
    "LoopeR": 7100,
    "Sharti72": 6600,
    "Alayy": 6400,
    "wish": 6400,
    "cod fish": 6300,
    "Falafel": 6300,
    "FrostyFeet": 5900,
    "Wolfe": 5900,
    "kirby griffin": 5100,
    "AoĐ": 5000,
    "Benny2402": 5000,
    "DiaZ": 4400,
    "P03": 4200,
    "Chienspecteur": 4000,
    "Hax": 3800,
    ".y": 3800,
    "Lke": 3300,
    "-MiKO--": 3300,
    "Shiden": 3100,
    "DuckyDuckDuck": 2900,
    "Doodles": 2800,
    "Ymir": 2800,
    "jjojehongg": 2600,
    "mr.tree": 2500,
    "viney": 2200,
    "tron": 2100,
    "bad girl": 1900,
    "N00B_bvt_Pro": 1900,
    "taizy": 1900,
    "Mersain": 1800,
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
    "zeboNik": 152,
    "(3": 149,
    "Nachos": 142,
    "bokoli": 133,
    "N3o": 130,
    "Doctor spine": 124,
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
    "disapointment": 42,
    "SirVitek": 40,
    "фкккееенннгггзззммm": 36,
    "Cheddi": 33,
    "Depressed MercyMain": 32,
    "purplehearts": 32,
    "Lilyboi": 30,
    "Arion_Wang": 27,
    "ReusableTpot": 27,
    "Articular": 26,
    "Pouyou": 26,
    "Rajeem": 22,
    "Pastel Princess": 22,
    "SunnyApple": 22,
    "ᐯㄖ 尺卩卂ㄥ": 20,
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
    "JustMercy": 6,
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
        if self.interaction.user.id != 141372217677053952:
            return
        await self.defer(ephemeral=True)
        if not await check_permissions(self.interaction):
            return
        logger.info(logging_util("Migration", "BEGIN EXP TRANSFER"))
        members = self.interaction.guild.members

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

            await ExperiencePoints.insert(
                ExperiencePoints(
                    user_id=member.id,
                    alias=member.name,
                    alerts_enabled=True,
                    xp=xp,
                    rank=rank,
                )
            )

        await self.interaction.edit_original_message(content="Done.")
