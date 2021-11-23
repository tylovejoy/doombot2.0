from beanie import Document, init_beanie
from typing import List
import motor


class Record(Document):
    user_id: int
    code: str
    level: str
    record: float
    verified: bool


class Map(Document):
    user_id: int
    code: str
    map_name: str
    map_type: List[str]

    @classmethod
    async def get_all_maps(cls, map_name):
        return await cls.find(cls.map_name == map_name).to_list()


async def database_init():
    client = motor.motor_asyncio.AsyncIOMotorClient(
        "mongodb://user:pass@host:27017"
    )

    await init_beanie(database=client.db_name, document_models=[Record, Map])