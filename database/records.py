from __future__ import annotations

from typing import Any, Generator, List, Optional, Set

import discord
from beanie import Document, Link
from beanie.odm.operators.find.evaluation import RegEx
from pydantic import BaseModel, Field

from database.maps import MapCodes, MapLevels


class AllLevelsSubAgg(Document):
    level: str


class AllLevelsAgg(BaseModel):
    """Projection model for World Records aggregation."""

    id: Link[AllLevelsSubAgg] = Field(None, alias="_id")


class WorldRecordsSubAggregate(Document):
    """Projection model for World Records aggregation."""

    code: str
    level: str
    url: str


class WorldRecordsAggregate(BaseModel):
    """Projection model for World Records aggregation."""

    id: Link[WorldRecordsSubAggregate] = Field(None, alias="_id")
    user_id: int
    record: float


class UniquePlayers(BaseModel):
    """Projection model for unique players in a Record aggregation."""

    name: str
    user_id: int

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name}, {self.user_id}"


class CurrentRecordPlacement(BaseModel):
    """Projection model for $rank mongo aggregation."""

    user_id: int
    rank: int


class MapDataLookup(BaseModel):
    """Projection model for $lookup with RecordMapLookup."""

    creator: str
    map_name: str


class RecordMapLookup(BaseModel):
    """Projection model for Record and Map data."""

    user_id: int
    code: str
    level: str
    record: float
    verified: str
    map_data: Optional[MapDataLookup]


class Record(Document):
    """Collection of personal best records."""

    user_id: int
    code: str
    level: str
    record: float
    verified: bool
    message_id: Optional[int]
    hidden_id: Optional[int]
    attachment_url: Optional[str] = Field("", alias="url")

    @classmethod
    async def all_levels(cls) -> List[AllLevelsAgg]:
        return (
            await cls.find()
            .aggregate(
                [{"$group": {"_id": {"level": "$level"}}}],
                projection_model=AllLevelsAgg,
            )
            .to_list()
        )

    @classmethod
    async def find_rec_map_info(cls, user_id):
        """Find record data as well as corresponding map data."""
        return (
            await cls.find(cls.user_id == user_id)
            .aggregate(
                [
                    {
                        "$lookup": {
                            "from": "Map",
                            "localField": "code",
                            "foreignField": "code",
                            "as": "map_data",
                        }
                    },
                    {
                        "$unwind": {
                            "path": "$map_data",
                            "preserveNullAndEmptyArrays": True,
                        }
                    },
                    {
                        "$project": {
                            "user_id": 1,
                            "code": 1,
                            "level": 1,
                            "record": 1,
                            "verified": 1,
                            "map_data.creator": 1,
                            "map_data.map_name": 1,
                        }
                    },
                    {"$sort": {"code": 1, "level": 1}},
                ],
                projection_model=RecordMapLookup,
            )
            .to_list()
        )

    @classmethod
    async def find_current_rank(
        cls, map_code: str, map_level: str, user_id: int
    ) -> List[CurrentRecordPlacement]:
        """Find the current rank placement of a record."""
        # TODO: Needs to be tested when Mongo is updated to 5.0
        return (
            await cls.find(cls.code == map_code, cls.level == map_level)
            .aggregate(
                [
                    {
                        "$setWindowFields": {"sortBy": {"record": 1}},
                        "output": {"rank": {"$rank": {}}},
                    },
                    {"$match": {"user_id": user_id}},
                ],
                projection_model=CurrentRecordPlacement,
            )
            .to_list()
        )

    @classmethod
    async def find_unique_players(cls) -> Set[str]:
        """Find unique players."""
        x = await cls.find().project(projection_model=UniquePlayers).to_list()
        return set(str(i) for i in x)

    @classmethod
    async def find_world_records_user(cls, user_id: int) -> List[WorldRecordsAggregate]:
        """Find all the world records that a user has."""
        return (
            await cls.find(cls.verified == True)
            .aggregate(
                [
                    {"$sort": {"record": 1}},
                    {
                        "$group": {
                            "_id": {"code": "$code", "level": "$level", "url": "$url"},
                            "record": {"$first": "$record"},
                            "user_id": {"$first": "$user_id"},
                        }
                    },
                    {"$match": {"user_id": user_id}},
                    {"$sort": {"_id.code": 1, "_id.level": 1}},
                ],
                projection_model=WorldRecordsAggregate,
            )
            .to_list()
        )

    @classmethod
    async def find_world_records(cls, **filters) -> WorldRecordsAggregate:
        """Find all the world records that a user has."""

        map_code = filters.get("map_code")
        verified = filters.get("verified")

        search_filter = {}

        if map_code:
            search_filter.update({"code": map_code})
        if verified:
            search_filter.update({"verified": verified})

        return (
            await cls.find(search_filter)
            .aggregate(
                [
                    {"$sort": {"record": 1}},
                    {
                        "$group": {
                            "_id": {"code": "$code", "level": "$level", "url": "$url"},
                            "record": {"$first": "$record"},
                            "user_id": {"$first": "$user_id"},
                        }
                    },
                    {"$sort": {"_id.level": 1}},
                ],
                projection_model=WorldRecordsAggregate,
            )
            .to_list()
        )

    @classmethod
    async def filter_search(cls, **filters: Any) -> List[Record]:
        """Get all amps with a particular filter."""
        search_filter = await cls.filter_search_(filters)
        return await cls.find(search_filter).sort("+code", "+level").to_list()

    @classmethod
    async def filter_search_single(cls, **filters: Any) -> Record:
        search_filter = await cls.filter_search_(filters)
        return await cls.find_one(search_filter)

    @classmethod
    async def filter_search_(cls, filters):
        map_code = filters.get("map_code")
        map_level = filters.get("map_level")
        user_id = filters.get("user_id")
        verified = filters.get("verified")
        search_filter = {}
        if map_code:
            search_filter.update({"code": map_code})
        if map_level:
            search_filter.update(
                RegEx("level", f"^{discord.utils.escape_markdown(map_level)}$")
            )
        if user_id:
            search_filter.update({"user_id": user_id})
        if verified:
            search_filter.update({"verified": verified})
        return search_filter

    @classmethod
    async def get_level_names(cls, map_code: str) -> List[str]:
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
    async def get_codes(cls, starts_with) -> Generator[tuple[Any, str], Any, None]:
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
        return ((x.get_data(), str(x)) for x in all_codes)
