from enum import Enum
from operator import itemgetter
from discord import PartialEmoji
from thefuzz import fuzz


class ExtendedEnum(Enum):
    """Base class for enums."""

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @classmethod
    def list(cls):
        """List of all values in the cls."""
        return sorted(list(map(lambda c: c.value, cls)))

    @classmethod
    def fuzz(cls, value):
        """Fuzz a value."""
        values = [
            (member, fuzz.partial_ratio(value, member.value))
            for name, member in cls.__members__.items()
        ]
        return str(max(values, key=itemgetter(1))[0])


class MapNames(ExtendedEnum):
    """An enum of Overwatch map names."""

    AYUTTHAYA = "Ayutthaya"
    BLACK_FOREST = "Black Forest"
    BLIZZARD_WORLD = "Blizzard World"
    BUSAN = "Busan"
    CASTILLO = "Castillo"
    CHATEAU_GUILLARD = "Chateau Guillard"
    DORADO = "Dorado"
    ECOPOINT_ANTARCTICA = "Ecopoint: Antarctica"
    EICHENWALDE = "Eichenwalde"
    HANAMURA = "Hanamura"
    HAVANA = "Havana"
    HOLLYWOOD = "Hollywood"
    HORIZON_LUNAR_COLONY = "Horizon Lunar Colony"
    ILIOS = "Ilios"
    JUNKERTOWN = "Junkertown"
    KANEZAKA = "Kanezaka"
    KINGS_ROW = "King's Row"
    LIJIANG_TOWER = "Lijiang Tower"
    MALEVENTO = "Malevento"
    NECROPOLIS = "Necropolis"
    NEPAL = "Nepal"
    NUMBANI = "Numbani"
    OASIS = "Oasis"
    PARIS = "Paris"
    PETRA = "Petra"
    PRACTICE_RANGE = "Practice Range"
    RIALTO = "Rialto"
    ROUTE_66 = "Route 66"
    TEMPLE_OF_ANUBIS = "Temple of Anubis"
    VOLSKAYA_INDUSTRIES = "Volskaya Industries"
    WATCHPOINT_GIBRALTAR = "Watchpoint: Gibraltar"
    WORKSHOP_CHAMBER = "Workshop Chamber"
    WORKSHOP_EXPANSE = "Workshop Expanse"
    WORKSHOP_GREEN_SCREEN = "Workshop Green Screen"
    WORKSHOP_ISLAND = "Workshop Island"
    FRAMEWORK = "Framework"
    TOOLS = "Tools"


class MapTypes(ExtendedEnum):
    """An enum of map types."""

    SINGLE = "Single"
    MULTI = "Multilevel"
    PIONEER = "Pioneer"
    TIME_ATTACK = "Time Attack"
    MEGAMAP = "Megamap"
    MULTI_MAP = "Multimap"
    TUTORIAL = "Tutorial"
    HARDCORE = "Hardcore"
    MILDCORE = "Mildcore"
    ABILITY_LOCK = "Ability Lock"
    SLAM_LOCK = "Slam Lock"
    NOSTALGIA = "Nostalgia"
    FRAMEWORK = "Framework"
    DIVERGE = "Diverge"
    BONUS = "Bonus"
    TOURNAMENT = "Tournament"
    OUT_OF_MAP = "Out of Map"
    TOOLS = "Tools"


class Emoji(Enum):
    """An enum of emojis."""

    VERIFIED = "✅"
    NOT_VERIFIED = "❌"
    TIME = "⌛"

    GOLD = "<:gold:931317421862699118>"
    DIAMOND = "<:diamond:931317455639445524>"
    GRANDMASTER = "<:grandmaster:931317469396729876>"

    @classmethod
    def is_verified(cls, value: bool):
        """Check for verification status. Return the proper emoji."""
        if value:
            return cls.VERIFIED
        return cls.NOT_VERIFIED

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @classmethod
    def display_rank(cls, value: str):
        if value == "Gold":
            return str(cls.GOLD)
        if value == "Diamond":
            return str(cls.DIAMOND)
        if value == "Grandmaster":
            return str(cls.GRANDMASTER)
        if value == "Unranked":
            return ""
