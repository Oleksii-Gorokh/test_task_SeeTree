from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


Score = Annotated[int, Field(ge=0, le=5)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
Latitude = Annotated[float, Field(ge=-90, le=90)]


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lng: Longitude
    lat: Latitude


class MarkerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coordinates: Coordinates
    score: Score = 0


class MarkerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coordinates: Coordinates | None = None
    score: Score | None = None


class Marker(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    coordinates: Coordinates
    score: Score
