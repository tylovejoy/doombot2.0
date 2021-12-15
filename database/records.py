from beanie import Document, Link
from beanie.odm.operators.find.evaluation import RegEx
from pydantic import BaseModel, Field

from database.maps import MapLevels, MapCodes


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
