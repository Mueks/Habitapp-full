from enum import Enum
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timezone, date
from typing import List, Optional


class HabitType(str, Enum):
    SIMPLE = "simple"
    FREQUENCY = "frequency"
    TIMER = "timer"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    google_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    picture_url: str | None = None
    google_access_token: str | None = Field(default=None)
    google_refresh_token: str | None = Field(default=None, index=True)
    google_token_expires_at: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)
    habits: List["Habit"] = Relationship(back_populates="user")


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    habit_type: HabitType = Field(default=HabitType.SIMPLE)
    frequency_count: int | None = Field(default=None)
    frequency_period: str | None = Field(default=None)
    target_minutes: int | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="habits")
    completions: List["HabitCompletion"] = Relationship(
        back_populates="habit", sa_relationship_kwargs={"cascade": "all, delete"}
    )


class HabitCompletion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    completion_date: date = Field(index=True)
    value: int | None = Field(default=None)
    habit_id: int | None = Field(default=None, foreign_key="habit.id")
    habit: Optional[Habit] = Relationship(back_populates="completions")
