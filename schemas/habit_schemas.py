from sqlmodel import SQLModel
from datetime import date, time
from models.habit_models import HabitType


class HabitBase(SQLModel):
    name: str
    description: str | None = None
    habit_type: HabitType = HabitType.SIMPLE
    frequency_count: int | None = None
    target_minutes: int | None = None
    scheduled_time: time | None = None
    duration_minutes: int | None = 60


class HabitCreate(HabitBase):
    sync_to_calendar: bool = False


class HabitUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    habit_type: HabitType | None = None
    frequency_count: int | None = None
    target_minutes: int | None = None
    scheduled_time: time | None = None
    duration_minutes: int | None = None


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


class HabitStats(SQLModel):
    """
    Representa las estadísticas calculadas para un hábito.
    """
    current_streak: int
    longest_streak: int
    total_completions: int
    completion_dates: list[date]


class HabitCompletionBulkCreate(SQLModel):
    dates: list[date]


class BulkResponse(SQLModel):
    entries_created: int
