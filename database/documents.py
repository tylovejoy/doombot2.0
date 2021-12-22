from logging import getLogger
from os import environ

import motor
from beanie import Document, init_beanie
from pydantic.main import BaseModel
from pymongo.errors import ServerSelectionTimeoutError

logger = getLogger(__name__)


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

    user_id: int
    alias: str
    alerts_enabled: bool
    rank: EXPRanks = EXPRanks()
    xp: int = 0

    @classmethod
    async def find_user(cls, user_id):
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
        logger.critical("Database connection failed..")
    else:
        logger.info("Database connection successful.")
