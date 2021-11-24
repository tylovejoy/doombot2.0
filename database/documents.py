import inspect
from os import environ

from beanie import Document, init_beanie
from typing import List
import motor
from logging import getLogger
from pymongo.errors import ServerSelectionTimeoutError

logger = getLogger(__name__)


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
    async def get_all_maps(cls, map_name: str) -> List["Map"]:
        """Get all maps with a particular map name."""
        return await cls.find(cls.map_name == map_name).to_list()

    @classmethod
    async def filter_search(cls, **filter: dict) -> List["Map"]:
        """Get all amps with a particulkar filter."""
        return await cls.find(filter).to_list()


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
