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
    email: str = Field(unique=True)
    full_name: str
    picture_url: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = Field(default=True)

    habits: List["Habit"] = Relationship(back_populates="user")


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None

    habit_type: HabitType = Field(default=HabitType.SIMPLE)

    # Estos campos solo son relevantes si habit_type es FREQUENCY
    frequency_count: int | None = Field(default=None)  # Ej: 8 (veces)
    frequency_period: str | None = Field(default=None)  # Ej: "day"

    # Estos campos solo son relevantes si habit_type es TIMER
    target_minutes: int | None = Field(default=None)  # Ej: 60 (minutos)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))

    # --- Llave foránea para la relación ---
    # Esto vincula cada hábito a un usuario.
    user_id: int | None = Field(default=None, foreign_key="user.id")

    # --- Relación de vuelta ---
    # Esto permite acceder al objeto User desde un objeto Habit.
    user: Optional[User] = Relationship(back_populates="habits")

    # Relación para que un hábito pueda acceder a su lista de completitudes.
    # El `cascade_delete` es útil: si borras un hábito, se borran sus registros.
    completions: List["HabitCompletion"] = Relationship(
        back_populates="habit", sa_relationship_kwargs={"cascade": "all, delete"}
    )


class HabitCompletion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    completion_date: date = Field(index=True)
    value: int | None = Field(default=None)
    habit_id: int | None = Field(default=None, foreign_key="habit.id")

    # Relación de vuelta para poder acceder al objeto Habit desde aquí.
    habit: Optional[Habit] = Relationship(back_populates="completions")
