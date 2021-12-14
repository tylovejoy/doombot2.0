from os import environ
from beanie import Document, init_beanie, Link
from typing import Any, List, Literal, Optional, Union
import motor
from logging import getLogger

from beanie.odm.operators.find.evaluation import RegEx
from pydantic import BaseModel, Field
from datetime import datetime
from pymongo.errors import ServerSelectionTimeoutError
from time import mktime

CategoryLiteral = Literal["ta", "mc", "hc", "bo"]

logger = getLogger(__name__)


class StoreItems(Document):

    """Collection of items to be bought."""

    item: str
    price: int

    @classmethod
    async def get_price(cls, item: str) -> int:
        """Get the price of an item."""
        return (await cls.find_one(cls.item == item)).price


class ExperiencePoints(Document):

    """Collection of user data."""

    user_id: int
    alias: str
    alerts_enabled: bool

    @classmethod
    async def find_user(cls, user_id):
        """Find a user."""
        return await cls.find_one(cls.user_id == user_id)

    @classmethod
    async def get_alias(cls, user_id: int) -> str:
        """Get an alias of a user."""
        return (await cls.find_user(user_id)).alias

    @classmethod
    async def is_alertable(cls, user_id: int) -> bool:
        """Get a bool of if the user is alertable."""
        return (await cls.find_user(user_id)).alerts_enabled

    @classmethod
    async def user_exists(cls, user_id: int) -> bool:
        """Check if the user exists."""
        return await cls.find_one(cls.user_id == user_id).exists()


class WorldRecordsSubAggregate(Document):

    """Projection model for World Records aggregation."""

    code: str
    level: str


class WorldRecordsAggregate(BaseModel):

    """Projection model for World Records aggregation."""

    id: Link[WorldRecordsSubAggregate] = Field(None, alias="_id")
    posted_by: int
    record: float


class UniquePlayers(BaseModel):

    """Projection model for unique players in a Record aggregation."""

    name: str
    posted_by: int

    def __str__(self):
        """String representation."""
        return f"{self.name}, {self.posted_by}"


class CurrentRecordPlacement(BaseModel):

    """Projection model for $rank mongo aggregation."""

    posted_by: int
    rank: int


class Record(Document):

    """Collection of personal best records."""

    posted_by: int  # TODO: user_id
    code: str
    level: str
    record: float
    verified: bool
    message_id: int
    hidden_id: int

    @classmethod
    async def find_current_rank(cls, map_code: str, map_level: str, user_id: int):
        """Find the current rank placement of a record."""
        return (
            await cls.find(cls.code == map_code, cls.level == map_level)
            .aggregate(
                [
                    {
                        "$setWindowFields": {"sortBy": {"record": 1}},
                        "output": {"rank": {"$rank": {}}},
                    },
                    {"$match": {"posted_by": user_id}},
                ],
                projection_model=CurrentRecordPlacement,
            )
            .to_list()
        )

    @classmethod
    async def find_unique_players(cls):
        """Find unique players."""
        x = await cls.find().project(projection_model=UniquePlayers).to_list()
        return set(str(i) for i in x)

    @classmethod
    async def find_world_records(cls, user_id: int):
        """Find all the world records that a user has."""
        return (
            await cls.find(cls.verified == True)
            .aggregate(
                [
                    {"$sort": {"record": 1}},
                    {
                        "$group": {
                            "_id": {"code": "$code", "level": "$level"},
                            "record": {"$first": "$record"},
                            "posted_by": {"$first": "$posted_by"},
                        }
                    },
                    {"$match": {"posted_by": user_id}},
                ],
                projection_model=WorldRecordsAggregate,
            )
            .to_list()
        )

    @classmethod
    async def find_record(cls, code: str, level: str, user_id: int) -> "Record":
        """Find a specific record."""
        return await cls.find_one(
            cls.code == code, cls.level == level, cls.posted_by == user_id
        )

    @classmethod
    async def get_level_names(cls, map_code: str):
        """Get the names of levels in a map code."""
        all_levels = (
            await cls.find(cls.code == map_code)
            .aggregate(
                [{"$project": {"level": 1}}, {"$sort": {"level": 1}}],
                projection_model=MapLevels,
            )
            .to_list()
        )
        return [str(x) for x in all_levels]

    @classmethod
    async def get_codes(cls, starts_with):
        """Get map codes that start with a specific string."""
        all_codes = (
            await cls.find(RegEx("code", "^" + starts_with, "i"))
            .aggregate(
                [
                    {"$project": {"code": 1}},
                    {"$sort": {"code": 1}},
                    {"$limit": 25},
                    {
                        "$lookup": {
                            "from": "Map",
                            "localField": "code",
                            "foreignField": "code",
                            "as": "map_data",
                        }
                    },
                ],
                projection_model=MapCodes,
            )
            .to_list()
        )
        print(list((str(x), x.get_data()) for x in all_codes))
        return ((x.get_data(), str(x)) for x in all_codes)


class MapLevels(BaseModel):

    """Projection model for Map aggregation."""

    level: str

    def __str__(self):
        """String representation."""
        return self.level


class MapCodes(BaseModel):

    """Project model for Map aggregation."""

    code: str
    map_data: list

    def __str__(self):
        """String representation."""
        return self.code

    def get_data(self):
        """Get the code and creator/map name if submitted to the database."""
        if self.map_data:
            return f"{self.code} -- ({self.map_data[0]['map_name']} by {self.map_data[0]['creator']})"
        return self.code


class Map(Document):

    """Collection of Maps."""

    user_id: int
    code: str
    creator: str
    map_name: str
    map_type: List[str]
    description: str

    @classmethod
    async def find_one_map(cls, map_code: str) -> "Map":
        """Find a single map using its workshop code."""
        return await cls.find_one(cls.code == map_code)

    @classmethod
    async def check_code(cls, map_code: str) -> bool:
        """Check if a map exists with specific map_code."""
        return await cls.find_one(cls.code == map_code).exists()

    @classmethod
    async def get_all_maps(cls, map_name: str) -> List["Map"]:
        """Get all maps with a particular map name."""
        return await cls.find(cls.map_name == map_name).to_list()

    @classmethod
    async def filter_search(cls, **filters: Any) -> List["Map"]:
        """Get all amps with a particular filter."""
        map_name = filters.get("map_name")
        map_type = filters.get("map_type")
        creator = filters.get("creator")

        search_filter = {}

        if map_name:
            search_filter.update({"map_name": map_name})
        if map_type:
            search_filter.update({"map_type": map_type})
        if creator:
            search_filter.update(RegEx("creator", creator, "i"))

        return await cls.find(search_filter).to_list()

    @classmethod
    async def random(cls, amount: int):
        """Find {amount} random maps."""
        return (
            await cls.find()
            .aggregate([{"$sample": {"size": amount}}], projection_model=cls)
            .to_list()
        )


class TournamentMaps(BaseModel):

    """Tournament data maps object."""

    code: str
    creator: str
    map_name: str
    

class TournamentRecords(BaseModel):
    """Base model for tournament records."""
    record: float
    posted_by: int
    attachment_url: str

class TournamentMissions(BaseModel):
    """Base model for tournament missions."""
    type: str
    target: str

class TournamentMissionsCategories(BaseModel):
    """Base model for tournament mission categories."""
    easy: Optional[TournamentMissions]
    medium: Optional[TournamentMissions]
    hard: Optional[TournamentMissions]
    expert: Optional[TournamentMissions]

class TournamentCategories(BaseModel):

    """Base models for tournament categories."""

    ta: Union[TournamentMaps, Optional[List[TournamentRecords]], Optional[TournamentMissionsCategories]]
    mc: Union[TournamentMaps, Optional[List[TournamentRecords]], Optional[TournamentMissionsCategories]]
    hc: Union[TournamentMaps, Optional[List[TournamentRecords]], Optional[TournamentMissionsCategories]]
    bo: Union[TournamentMaps, Optional[List[TournamentRecords]], Optional[TournamentMissionsCategories]]


class Tournament(Document):

    """Collection of Tournament data."""

    tournament_id: int
    name: str
    active: bool
    bracket: bool
    bracket_category: Optional[str]
    schedule_start: datetime
    schedule_end: datetime

    maps: TournamentCategories
    records: TournamentCategories
    missions: TournamentCategories

    @staticmethod
    def get_unix_timestamp(dt: datetime) -> str:
        return str(mktime(dt.timetuple()))

    @classmethod
    async def find_latest(cls):
        return await cls.find().sort(-cls.tournament_id).limit(1).to_list()

    def get_map_str(self, category: CategoryLiteral) -> str:
        return f"{self.maps[category]['code']} - {self.maps[category]['level']} by {self.maps[category]['author']}\n"

    def get_all_map_str(self) -> str:
        return (
            self.get_map_str("ta") + 
            self.get_map_str("mc") + 
            self.get_map_str("hc") +
            self.get_map_str("bo")
        )

    def get_records(self, category: CategoryLiteral) -> List[TournamentRecords]:
        return self.records[category]

    def get_unix_start(self):
        return self.get_unix_timestamp(self.schedule_start)

    def get_unix_end(self):
        return self.get_unix_timestamp(self.schedule_end)


DB_PASSWORD = environ["DB_PASSWORD"]


async def database_init():
    """Initialize mongo database."""
    client = motor.motor_asyncio.AsyncIOMotorClient(
        f"mongodb+srv://mapbot:{DB_PASSWORD}@mapbot.oult0.mongodb.net/doombot?retryWrites=true&w=majority"
    )

    try:
        await init_beanie(
            database=client.doombot, document_models=Document.__subclasses__()
        )
    except ServerSelectionTimeoutError:
        logger.critical("Database connection failed..")
    else:
        logger.info("Database connection successful.")
