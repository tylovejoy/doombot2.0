from __future__ import annotations

import datetime
from enum import unique
from logging import getLogger
from os import environ
from typing import Dict, List, Optional, Union
from unicodedata import category

import motor
from beanie import Document, init_beanie
from beanie.odm.fields import Indexed
from pydantic.main import BaseModel
from pymongo.errors import ServerSelectionTimeoutError

logger = getLogger(__name__)


class Voting(Document):
    """Collection of Votes."""

    user_id: int
    message_id: int
    channel_id: int
    anonymity: int
    voters: Optional[Dict[str, int]] = {}
    choices: Optional[Dict[str, int]] = {}


class ColorRoles(Document):
    """Collection of colors roles."""

    emoji: str
    label: str
    role_id: int
    sort_order: int


class Events(Document):
    """Collection of events."""

    event_id: int
    event_name: str
    schedule_start: datetime.datetime
    started: bool
    text: Optional[int]
    voice: Optional[int]
    category: Optional[int]


class VerificationViews(Document):
    """Collection of unattended verifications to persist thru restart."""

    message_id: int


class TagCategories(BaseModel):
    category: str


class TagNamesProjection(BaseModel):
    name: str


class Tags(Document):
    """Collection of Tags."""

    name: Indexed(str, unique=True)
    content: str
    category: str

    @classmethod
    async def find_all_tag_names(cls, category) -> List[str]:
        tags = (
            await cls.find(cls.category == category)
            .project(TagNamesProjection)
            .to_list()
        )
        return [x.name for x in tags]

    @classmethod
    async def exists(cls, name: str, category: str) -> bool:
        """Check if document exists."""
        return bool(await cls.find_one(cls.name == name, cls.category == category))

    @classmethod
    async def find_all_tag_categories(cls) -> List[str]:
        tags = await cls.find().project(TagCategories).to_list()
        categories = set()
        for t in tags:
            categories.add(t.category)
        return sorted(categories)


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
    bo: str = "Grandmaster"


class XPOnly(BaseModel):
    user_id: Indexed(int, unique=True)
    alias: str
    xp: int


class ExperiencePoints(Document):
    """Collection of user data."""

    user_id: Indexed(int, unique=True)
    alias: str
    alerts_enabled: bool
    rank: EXPRanks = EXPRanks()
    xp: int = 0
    xp_avg: Union[Optional[List], Optional[Dict[str, List[int]]]] = {
        "ta": [0, 0, 0, 0, 0],  # TA
        "mc": [0, 0, 0, 0, 0],  # MC
        "hc": [0, 0, 0, 0, 0],  # HC
        "bo": [0, 0, 0, 0, 0],  # BO
    }
    verified_count: int = 0
    dont_submit: Optional[bool] = False
    therapy_banned: Optional[bool] = False
    wins: Optional[int]
    losses: Optional[int]

    async def increment_verified(self) -> int:
        self.verified_count += 1
        await self.save()
        return self.verified_count

    async def check_if_unranked(self, category: str) -> bool:
        """Return True if user is unranked in category."""
        return getattr(self.rank, category) == "Unranked"

    @classmethod
    async def xp_leaderboard(cls) -> ExperiencePoints:
        return await cls.find().sort("-xp").project(XPOnly).to_list()

    @classmethod
    async def find_user(cls, user_id: int) -> ExperiencePoints:
        """Find a user."""
        return await cls.find_one(cls.user_id == user_id)

    @classmethod
    async def add_win(cls, user_id: int):
        user = await cls.find_user(user_id)
        user.wins += 1
        await user.save()

    @classmethod
    async def add_loss(cls, user_id: int):
        user = await cls.find_user(user_id)
        user.losses += 1
        await user.save()

    @classmethod
    async def change_xp(cls, user_id: int, amount: int):
        """Change a user's XP by a specific amount."""
        user: ExperiencePoints = await cls.find_one(cls.user_id == user_id)
        user.xp += amount
        await user.save()

    @classmethod
    async def duel_end(cls, *, winner: int, loser: int, wager: int):
        """Deal duel earnings and incremement W/L."""
        await cls.change_xp(winner, wager)
        await cls.change_xp(loser, -wager)
        await cls.add_win(winner)
        await cls.add_loss(loser)

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


class Guide(Document):
    """Collection of guides."""

    code: str
    guide: List[str] = []
    guide_owner: List[int] = []


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
