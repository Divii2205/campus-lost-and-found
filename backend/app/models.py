from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Item(Base):
    """one lost or found item reported on campus"""

    # name of the table in the database
    __tablename__ = "items"

    # each line below is one column in the table
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(30), default="OTHER")
    # status has an index so filtering by status is fast
    status: Mapped[str] = mapped_column(String(20), default="LOST", index=True)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    reporter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str] = mapped_column(String(120), nullable=False)
    # empty until someone claims the item
    claimed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # the time the item was reported in utc time
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
