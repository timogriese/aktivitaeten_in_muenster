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
    """What the scraper sends to the backend: an activity without server-assigned fields."""


class Activity(ActivityBase):
    """An activity as stored/returned by the backend."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
