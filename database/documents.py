from os import environ
from beanie import Document, init_beanie
from typing import Any, List
import motor
from logging import getLogger

from beanie.odm.operators.find.evaluation import RegEx
from pydantic import BaseModel
from pymongo.errors import ServerSelectionTimeoutError

logger = getLogger(__name__)


class StoreItems(Document):
    item: str
    price: int

    @classmethod
    async def get_price(cls, item: str) -> int:
        return (await cls.find_one(cls.item == item)).price


class ExperiencePoints(Document):
    user_id: int
    alias: str
    alerts_enabled: bool

    @classmethod
    async def find_user(cls, user_id):
        return await cls.find_one(cls.user_id == user_id)

    @classmethod
    async def get_alias(cls, user_id: int) -> str:
        return (await cls.find_user(user_id)).alias

    @classmethod
    async def is_alertable(cls, user_id: int) -> bool:
        return (await cls.find_user(user_id)).alerts_enabled

    @classmethod
    async def user_exists(cls, user_id: int) -> bool:
        return await cls.find_one(cls.user_id == user_id).exists()


class Record(Document):
    posted_by: int  # TODO: user_id
    code: str
    level: str
    record: float
    verified: bool
    message_id: int
    hidden_id: int

    @classmethod
    async def find_record(cls, code: str, level: str, user_id: int) -> "Record":
        return await cls.find_one(
            cls.code == code, cls.level == level, cls.posted_by == user_id
        )

    @classmethod
    async def get_level_names(cls, map_code: str):
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
    level: str

    def __str__(self):
        return self.level


class MapCodes(BaseModel):
    code: str
    map_data: list

    def __str__(self):
        return self.code

    def get_data(self):
        if self.map_data:
            return f"{self.code} -- ({self.map_data[0]['map_name']} by {self.map_data[0]['creator']})"
        return self.code


class Map(Document):
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


DB_PASSWORD = environ["DB_PASSWORD"]


async def database_init():
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
