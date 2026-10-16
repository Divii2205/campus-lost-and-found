from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# the only allowed values for status and category
Status = Literal["LOST", "FOUND", "CLAIMED"]
Category = Literal["ELECTRONICS", "BOOKS", "ID_CARD", "CLOTHING", "KEYS", "BOTTLE", "OTHER"]


# the data needed to report a new item
# field rules check the length of each text
class ItemCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=1000)
    category: Category = "OTHER"
    # a new report can only be lost or found
    status: Literal["LOST", "FOUND"] = "LOST"
    location: str = Field(min_length=2, max_length=120)
    reporter_name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=3, max_length=120)


# the data for changing an item
# every field is optional so you can change just one thing
class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    category: Category | None = None
    status: Status | None = None
    location: str | None = Field(default=None, min_length=2, max_length=120)
    reporter_name: str | None = Field(default=None, min_length=2, max_length=100)
    contact: str | None = Field(default=None, min_length=3, max_length=120)


# the name of the person who claims the item
class ClaimIn(BaseModel):
    claimed_by: str = Field(min_length=2, max_length=100)


# the item data the api sends back
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
    # lets this read data straight from a database item
    model_config = ConfigDict(from_attributes=True)


# the counts sent back by the stats route
class StatsOut(BaseModel):
    total: int
    lost: int
    found: int
    claimed: int
