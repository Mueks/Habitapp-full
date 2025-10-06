from sqlmodel import SQLModel
from datetime import date
from models import HabitType


class HabitBase(SQLModel):
    name: str
    description: str | None = None
    habit_type: HabitType = HabitType.SIMPLE
    frequency_count: int | None = None
    target_minutes: int | None = None


class HabitCreate(HabitBase):
    pass


class HabitUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    habit_type: HabitType | None = None
    frequency_count: int | None = None
    target_minutes: int | None = None


class HabitRead(HabitBase):
    id: int
    user_id: int


class HabitCompletionRead(SQLModel):
    id: int
    completion_date: date
    habit_id: int
    value: int | None = None


class HabitCompletionCreate(SQLModel):
    completion_date: date | None = None


class HabitTrack(SQLModel):
    value: int
