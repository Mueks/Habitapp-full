from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.habit_models import Habit


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    google_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    picture_url: str | None = None
    timezone: str | None = Field(default=None)
    google_access_token: str | None = Field(default=None)
    google_refresh_token: str | None = Field(default=None, index=True)
    google_token_expires_at: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)
    habits: List["Habit"] = Relationship(back_populates="user")
