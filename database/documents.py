from __future__ import annotations
from logging import getLogger
from os import environ
from typing import List, Optional
from beanie.odm.fields import Indexed

import motor
from beanie import Document, init_beanie
from pydantic.main import BaseModel
from pymongo.errors import ServerSelectionTimeoutError

logger = getLogger(__name__)


class VerificationViews(Document):
    """Collection of unattended verifications to persist thru restart."""

    message_id: int


class TagNamesProjection(BaseModel):
    name: str


class Tags(Document):
    """Collection of Tags."""

    name: Indexed(str, unique=True)
    content: str

    @classmethod
    async def find_all_tag_names(cls) -> List[str]:
        tags = await cls.find().project(TagNamesProjection).to_list()
        return [x.name for x in tags]


class Starboard(Document):
    """Collection of suggestions."""

    stars: int = 0
    jump: str
    message_id: Indexed(int, unique=True)
    starboard_id: int = 0
    reacted: List[int] = []

    @classmethod
    async def search(cls, id_):
        return await cls.find_one(cls.message_id == id_)


class StoreItems(Document):
    """Collection of items to be bought."""

    item: str
    price: int

    @classmethod
    async def get_price(cls, item: str) -> int:
        """Get the price of an item."""
        return (await cls.find_one(cls.item == item)).price


class EXPRanks(BaseModel):
    """Per user ranks."""

    ta: str = "Unranked"
    mc: str = "Unranked"
    hc: str = "Unranked"
    bo: str = "Unranked"


class ExperiencePoints(Document):
    """Collection of user data."""

    user_id: Indexed(int, unique=True)
    alias: str
    alerts_enabled: bool
    rank: EXPRanks = EXPRanks()
    xp: int = 0
    xp_avg: List[Optional[int]] = [0, 0, 0, 0, 0]
    verified_count: int = 0

    async def increment_verified(self) -> int:
        self.verified_count += 1
        await self.save()
        return self.verified_count

    async def check_if_unranked(self, category: str) -> bool:
        return getattr(self.rank, category) == "Unranked"

    @classmethod
    async def find_user(cls, user_id) -> ExperiencePoints:
        """Find a user."""
        return await cls.find_one(cls.user_id == user_id)

    @classmethod
    async def get_alias(cls, user_id: int) -> str:
        """Get an alias of a user."""
        user = await cls.find_user(user_id)
        if user:
            return user.alias
        return "No name"

    @classmethod
    async def is_alertable(cls, user_id: int) -> bool:
        """Get a bool of if the user is alertable."""
        return (await cls.find_user(user_id)).alerts_enabled

    @classmethod
    async def user_exists(cls, user_id: int) -> bool:
        """Check if the user exists."""
        return await cls.find_one(cls.user_id == user_id).exists()


DB_PASSWORD = environ["DB_PASSWORD"]


# noinspection SpellCheckingInspection
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
        logger.critical("Connecting database - FAILED!!!")

    else:
        logger.info("Connecting database - SUCCESS!")
