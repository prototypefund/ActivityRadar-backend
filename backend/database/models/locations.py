from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import GEOSPHERE, IndexModel

from backend.database.models.shared import (
    CreationInfo,
    GeoJSONLocation,
    GeoJSONObject,
    PhotoInfo,
    Review,
)

class LocationBase(BaseModel):
    activity_type: str
    location: GeoJSONLocation

class LocationShort(LocationBase):
    name: str | None
    trust_score: int

class LocationDetailed(LocationShort):
    tags: dict[str, Any]
    recent_reviews: list[Review]
    geometry: GeoJSONObject | None
    photos: list[PhotoInfo] | None

class LocationDetailedDB(Document, LocationDetailed):
    creation: CreationInfo
    last_modified: datetime
    osm_id: int | None = None

    class Settings:
        name = "locations"
        indexes = [
            "osm_id",
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationShortDB(Document, LocationShort):
    class Settings:
        name = "simple_locations"
        indexes = [
            "activity_type",
            IndexModel([("location", GEOSPHERE)],
                       name="location_index_GEO")
        ]

class LocationNew(LocationBase):
    name: str | None = None
    photos: list[PhotoInfo] = []
    tags: dict[str, Any] = {}
    geometry: GeoJSONObject | None = None

class LocationShortAPI(LocationBase):
    id: PydanticObjectId

class LocationDetailedAPI(LocationDetailed):
    ...

class LocationHistory(Document):
    pass

