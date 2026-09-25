from __future__ import annotations

from datetime import date as date_
from datetime import datetime, time
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class GroupType(str, Enum):
    joinable_group = "joinable_group"
    self_organized = "self_organized"


class Location(BaseModel):
    address: str
    lat: float
    lon: float


class OpeningHours(BaseModel):
    date: date_ | None = None
    start: time
    end: time


class Source(BaseModel):
    type: Literal["scraped", "user_submitted", "ai_suggested"]
    url: str | None = None
    scraped_at: datetime | None = None
    extraction_confidence: float | None = None


class ActivityBase(BaseModel):
    title: str
    description: str
    category: str
    tags: list[str] = Field(default_factory=list)
    location: Location
    group_type: GroupType
    opening_hours: OpeningHours
    price_eur: float
    source: Source


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    location: Location | None = None
    group_type: GroupType | None = None
    opening_hours: OpeningHours | None = None
    price_eur: float | None = None
    source: Source | None = None


class Activity(ActivityBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
