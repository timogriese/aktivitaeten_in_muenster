from __future__ import annotations

from datetime import date as date_
from datetime import time
from typing import Literal

from pydantic import BaseModel, Field

from app.models.activity import GroupType

Category = Literal["sport", "nature", "culture", "music", "creative", "food", "market", "social"]
Weekday = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class ExtractedActivity(BaseModel):
    """What the LLM returns for one page - the extraction contract, not the backend's.

    ScraperService turns this into an ActivityCreate: it geocodes the address, derives the
    date for weekly sessions, filters tags against shared/tags.json and rejects entries
    whose times aren't backed by the page.
    """

    title: str = Field(description="Concrete name, in German unless it's a proper name")
    description: str = Field(description="1-3 sentences in German")
    category: Category
    tags: list[str] = Field(description="Any number of fitting tags, only from the allowed list")
    address: str = Field(description="Street + house number (or named place) + Münster")
    group_type: GroupType
    date: date_ | None = Field(default=None, description="Only for a one-time event")
    weekdays: list[Weekday] = Field(
        default_factory=list,
        description="Weekdays of a recurring session; empty = every day / not weekday-bound",
    )
    start: time | None = None
    end: time | None = None
    times_stated: bool = Field(description="True only if start/end are written on the page")
    price_eur: float | None = Field(default=None, description="null if the page states no price")
