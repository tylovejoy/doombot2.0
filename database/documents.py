from os import environ
from beanie import Document, init_beanie
from typing import Any, List
import motor
from logging import getLogger

from beanie.odm.operators.find.evaluation import RegEx
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

    @classmethod
    async def get_alias(cls, user_id: int) -> str:
        return (await cls.find_one(cls.user_id == user_id)).alias


class Record(Document):
    user_id: int
    code: str
    level: str
    record: float
    verified: bool


class Map(Document):
    user_id: int
    code: str
    creator: str
    map_name: str
    map_type: List[str]
    description: str

    @classmethod
    async def check_code(cls, map_code: str) -> bool:
        return await cls.find(cls.code == map_code).exists()

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
    async def random(cls):
        return await cls.find().aggregate(
            [{"$sample": {"size": 1}}], projection_model=cls
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
