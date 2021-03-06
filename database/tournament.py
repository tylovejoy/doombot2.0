from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Generator, List, Literal, Optional, Union

from beanie import Document
from beanie.odm.operators.find.logical import Or
from discord.utils import MISSING
from pydantic import BaseModel

from database.documents import EXPRanks
from utils.utilities import format_missions, tournament_category_map

CategoryLiteral = Literal["ta", "mc", "hc", "bo"]
DifficultyLiteral = Literal["easy", "medium", "hard", "expert"]

logger = getLogger(__name__)


class Announcement(Document):
    """Scheduled announcements."""

    embed: dict
    schedule: datetime
    mentions: str


class TournamentMaps(BaseModel):
    """Tournament data maps object."""

    code: str
    creator: str
    level: str


class TournamentRecords(BaseModel):
    """Base model for tournament records."""

    record: float
    user_id: int
    attachment_url: str


class TournamentMissions(BaseModel):
    """Base model for tournament missions."""

    type: Optional[str]
    target: Optional[Union[str, int, float]]


class TournamentMissionsCategories(BaseModel):
    """Base model for tournament mission categories."""

    easy: TournamentMissions = TournamentMissions()
    medium: TournamentMissions = TournamentMissions()
    hard: TournamentMissions = TournamentMissions()
    expert: TournamentMissions = TournamentMissions()


class TournamentData(BaseModel):
    """Base models for tournament categories."""

    map_data: TournamentMaps
    records: List[Optional[TournamentRecords]] = []
    missions: TournamentMissionsCategories = TournamentMissionsCategories()


class ShorterRecordData(BaseModel):
    record: float
    user_id: int
    attachment_url: str


class ShortRecordData(BaseModel):
    records: ShorterRecordData


class ShortUserData(BaseModel):
    alias: str
    rank: EXPRanks


class TournamentRecordsLookup(BaseModel):
    ta: Optional[ShortRecordData]
    mc: Optional[ShortRecordData]
    hc: Optional[ShortRecordData]
    bo: Optional[ShortRecordData]
    user_data: Optional[ShortUserData]


class Tournament(Document):
    """Collection of Tournament data."""

    tournament_id: int
    name: str
    active: bool
    bracket: Optional[bool]
    embed: Optional[dict]
    mentions: Optional[str]
    schedule_start: datetime
    schedule_end: datetime

    ta: Optional[TournamentData]
    mc: Optional[TournamentData]
    hc: Optional[TournamentData]
    bo: Optional[TournamentData]

    general: List[Optional[TournamentMissions]] = []

    xp: Optional[dict]

    @classmethod
    async def find_active(cls) -> Tournament:
        return await cls.find_one(cls.active == True)

    @classmethod
    async def find_latest(cls) -> Tournament:
        t = await cls.find().sort("-tournament_id").limit(1).to_list()
        return t[0] if t else None

    @classmethod
    async def get_records(
        cls, category, rank=MISSING
    ) -> List[Optional[TournamentRecordsLookup]]:
        aggregation = [
            {"$sort": {"tournament_id": -1}},
            {"$limit": 1},
            {"$project": {f"{category}.records": 1}},
            {"$unwind": {"path": f"${category}.records"}},
            {"$sort": {f"{category}.records": 1}},
            {
                "$lookup": {
                    "from": "ExperiencePoints",
                    "localField": f"{category}.records.user_id",
                    "foreignField": "user_id",
                    "as": "user_data",
                }
            },
            {"$unwind": {"path": "$user_data", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    f"{category}.records": 1,
                    "user_data.alias": 1,
                    "user_data.rank": 1,
                }
            },
        ]
        if rank is not MISSING:
            aggregation.append({"$match": {f"user_data.rank.{category}": f"{rank}"}})

        return (
            await cls.find()
            .aggregate(aggregation, projection_model=TournamentRecordsLookup)
            .to_list()
        )

    def get_categories(self) -> Generator[str]:
        for cat in ["ta", "mc", "hc", "bo"]:
            if getattr(self, cat, None):
                yield cat

    def get_map_str(self, category: CategoryLiteral) -> str:
        category = getattr(self, category, None)
        return (
            f"{category.map_data.code} - {category.map_data.level} "
            f"({category.map_data.map_name}) by {category.map_data.creator}\n"
        )

    def get_all_map_str(self) -> str:
        map_string = ""
        for category in self.get_categories():
            map_string += self.get_map_str(category)
        return map_string

    def get_map_str_short(self, category: str) -> str:
        category = getattr(self, category, None)
        return f"({category.map_data.code} - {category.map_data.level})"

    def get_category_missions(self, category: CategoryLiteral) -> str:
        obj = getattr(self, category, None).missions
        missions = ""
        for difficulty in ["easy", "medium", "hard", "expert"]:
            mission = getattr(obj, difficulty, None)
            if not mission.type:
                continue
            missions += f"- {difficulty.capitalize()}: " + format_missions(
                mission.type, mission.target
            )

        return missions + "\n"

    def get_all_missions(self) -> str:
        missions = ""
        # General
        missions += self.get_general() + "\n"
        # Categories
        categories = list(self.get_categories())
        for category in categories:
            missions += f"**{tournament_category_map(category)} {self.get_map_str_short(category)}**\n"
            missions += self.get_category_missions(category)

        return missions

    def get_general(self) -> str:
        missions = "**General:**\n"
        for mission in self.general:
            missions += f"- {format_missions(mission.type, mission.target)}"
        return missions


class DuelPlayer(BaseModel):
    """Player in duel."""

    user_id: int
    record: Optional[float]
    attachment_url: Optional[str]
    ready: bool


class Duel(Document):
    """Duel."""

    player1: DuelPlayer
    player2: DuelPlayer
    message: int
    channel_msg: int
    thread: int
    wager: int
    standby_time: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]

    @classmethod
    async def find_duel(cls, user_id) -> Duel:
        return await cls.find_one(
            Or(cls.player1.user_id == user_id, cls.player2.user_id == user_id)
        )

    @classmethod
    async def find_duel_thread(cls, user_id: int, thread_id: int) -> Duel:
        return await cls.find_one(
            cls.player2.user_id == user_id, cls.thread == thread_id
        )

    @classmethod
    async def find_duel_thread_two_players(cls, user_id: int, thread_id: int) -> Duel:
        return await cls.find_one(
            Or(cls.player2.user_id == user_id, cls.player1.user_id == user_id),
            cls.thread == thread_id,
        )

    @classmethod
    async def find_duel_thread_only(cls, thread_id: int) -> Duel:
        return await cls.find_one(cls.thread == thread_id)
