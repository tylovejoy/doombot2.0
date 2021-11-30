from enum import Enum
from operator import itemgetter
from thefuzz import fuzz


class ExtendedEnum(Enum):
    def __str__(self) -> str:
        return self.value

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def fuzz(cls, value):
        values = [
            (member, fuzz.partial_ratio(value, member.value))
            for name, member in cls.__members__.items()
        ]
        return max(values, key=itemgetter(1))[0]


class MapNames(ExtendedEnum):

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


class MapTypes(ExtendedEnum):

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
