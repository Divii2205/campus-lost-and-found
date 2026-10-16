from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["LOST", "FOUND", "CLAIMED"]
Category = Literal["ELECTRONICS", "BOOKS", "ID_CARD", "CLOTHING", "KEYS", "BOTTLE", "OTHER"]


class ItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=1000)
    category: Category = "OTHER"
    status: Literal["LOST", "FOUND"] = "LOST"
    location: str = Field(min_length=2, max_length=120)
    reporter_name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=3, max_length=120)


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    category: Category | None = None
    status: Status | None = None
    location: str | None = Field(default=None, min_length=2, max_length=120)
    reporter_name: str | None = Field(default=None, min_length=2, max_length=100)
    contact: str | None = Field(default=None, min_length=3, max_length=120)


class ClaimIn(BaseModel):
    claimed_by: str = Field(min_length=2, max_length=100)


class ItemOut(BaseModel):
    id: int
    title: str
    description: str
    category: Category
    status: Status
    location: str
    reporter_name: str
    contact: str
    claimed_by: str | None
    reported_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total: int
    lost: int
    found: int
    claimed: int
