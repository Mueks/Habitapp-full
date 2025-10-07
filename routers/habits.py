from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import date, timedelta

from database import get_session
from models import User, Habit, HabitCompletion
from auth_utils import get_current_user
from schemas import HabitCompletionCreate, HabitCreate, HabitRead, HabitUpdate, HabitCompletionRead, HabitTrack, HabitStats, HabitCompletionBulkCreate, BulkResponse

from calendar_services import create_calendar_event_for_habit

router = APIRouter(prefix="/habits", tags=["Habits"])


# --- Dependencia ---
def get_valid_habit_for_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    habit_id: int
) -> Habit:
    """
    Dependencia que obtiene un hábito por ID y verifica que pertenezca
    al usuario autenticado. Devuelve el objeto Habit o lanza una excepción.
    """
    habit = session.get(Habit, habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hábito no encontrado")
    if habit.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No tienes permiso para esta acción")
    return habit


@router.post("/", response_model=HabitRead)
async def create_habit(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    habit_in: HabitCreate
):
    """Crea un nuevo hábito para el usuario autenticado."""
    habit = Habit.model_validate(habit_in, update={"user_id": current_user.id})
    session.add(habit)
    session.commit()
    session.refresh(habit)

    if habit_in.sync_to_calendar:
        await create_calendar_event_for_habit(current_user, habit, date.today())

    return habit


@router.get("/", response_model=List[HabitRead])
def get_user_habits(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Obtiene todos los hábitos del usuario autenticado."""
    statement = select(Habit).where(Habit.user_id == current_user.id)
    habits = session.exec(statement).all()
    return habits


@router.get("/{habit_id}", response_model=HabitRead)
def get_habit_by_id(habit: Habit = Depends(get_valid_habit_for_user)):
    """Obtiene un hábito específico por su ID usando la dependencia."""
    return habit


@router.patch("/{habit_id}", response_model=HabitRead)
def update_habit_by_id(
    *,
    session: Session = Depends(get_session),
    habit_in: HabitUpdate,
    habit: Habit = Depends(get_valid_habit_for_user)
):
    """
    Actualiza parcialmente un hábito por su ID.
    """
    update_data = habit_in.model_dump(exclude_unset=True)
    habit.sqlmodel_update(update_data)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit_by_id(
    *,
    session: Session = Depends(get_session),
    habit: Habit = Depends(get_valid_habit_for_user)  # Y aquí también
):
    """Elimina un hábito por su ID usando la dependencia."""
    session.delete(habit)
    session.commit()

    return None


@router.post("/{habit_id}/complete", response_model=HabitCompletionRead)
def mark_habit_as_complete(
    *,
    session: Session = Depends(get_session),

    habit: Habit = Depends(get_valid_habit_for_user),
    completion_in: HabitCompletionCreate
):
    """
    Marca un hábito como completado para una fecha específica (por defecto, hoy).
    Evita que se marque como completado dos veces en el mismo día.
    """

    completion_date = completion_in.completion_date or date.today()

    statement = select(HabitCompletion).where(
        HabitCompletion.habit_id == habit.id,
        HabitCompletion.completion_date == completion_date
    )
    existing_completion = session.exec(statement).first()

    if existing_completion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El hábito ya fue marcado como completado para esta fecha."
        )

    db_completion = HabitCompletion(
        habit_id=habit.id,
        completion_date=completion_date
    )

    session.add(db_completion)
    session.commit()
    session.refresh(db_completion)

    return db_completion


@router.delete("/{habit_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def unmark_habit_as_complete(
    *,
    session: Session = Depends(get_session),
    habit: Habit = Depends(get_valid_habit_for_user),
    completion_date: date | None = None
):
    """
    Elimina el registro de completitud de un hábito para una fecha específica (por defecto, hoy).
    """
    target_date = completion_date or date.today()

    statement = select(HabitCompletion).where(
        HabitCompletion.habit_id == habit.id,
        HabitCompletion.completion_date == target_date
    )
    completion_to_delete = session.exec(statement).first()

    if not completion_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un registro de completitud para esta fecha."
        )

    session.delete(completion_to_delete)
    session.commit()
    return None


@router.get("/{habit_id}/completions", response_model=List[HabitCompletionRead])
def get_habit_completions(
    *,
    habit: Habit = Depends(get_valid_habit_for_user)
):
    """
    Obtiene el historial de completitud de un hábito específico.
    """

    return habit.completions


@router.post("/{habit_id}/track", response_model=HabitCompletionRead)
def track_habit_progress(
    *,
    session: Session = Depends(get_session),
    habit: Habit = Depends(get_valid_habit_for_user),
    track_in: HabitTrack
):
    """
    Registra progreso para un hábito de frecuencia o temporizador.
    Si ya existe un registro para hoy, le suma el valor. Si no, lo crea.
    """
    today = date.today()

    statement = select(HabitCompletion).where(
        HabitCompletion.habit_id == habit.id,
        HabitCompletion.completion_date == today
    )
    db_completion = session.exec(statement).first()

    if db_completion:

        db_completion.value = (db_completion.value or 0) + track_in.value
    else:

        db_completion = HabitCompletion(
            habit_id=habit.id,
            completion_date=today,
            value=track_in.value
        )

    session.add(db_completion)
    session.commit()
    session.refresh(db_completion)

    return db_completion


@router.get("/{habit_id}/stats", response_model=HabitStats)
def get_habit_stats(
    habit: Habit = Depends(get_valid_habit_for_user)
):
    """
    Calcula y devuelve estadísticas clave para un hábito específico,
    como la racha actual, la racha más larga y el total de completitudes.
    """
    completion_dates = sorted(
        list(set(c.completion_date for c in habit.completions)))

    if not completion_dates:
        return HabitStats(
            current_streak=0,
            longest_streak=0,
            total_completions=0,
            completion_dates=[]
        )

    total_completions = len(completion_dates)

    longest_streak = 0
    current_streak = 0

    if total_completions > 0:

        longest_streak = 1
        streak_so_far = 1

        for i in range(1, total_completions):

            consecutive_day = completion_dates[i] == completion_dates[i-1] + timedelta(
                days=1)

            if consecutive_day:
                streak_so_far += 1
            else:
                streak_so_far = 1

            if streak_so_far > longest_streak:
                longest_streak = streak_so_far

        today = date.today()
        last_completion_date = completion_dates[-1]

        if last_completion_date == today or last_completion_date == today - timedelta(days=1):
            current_streak = streak_so_far
        else:
            current_streak = 0

    return HabitStats(
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_completions=total_completions,
        completion_dates=completion_dates
    )


@router.post("/{habit_id}/completions/bulk", response_model=BulkResponse)
def create_bulk_completions(
    *,
    session: Session = Depends(get_session),
    habit: Habit = Depends(get_valid_habit_for_user),
    bulk_in: HabitCompletionBulkCreate
):
    """
    Crea múltiples registros de completitud para un hábito a partir de una lista de fechas.
    Evita la creación de duplicados si una fecha ya está registrada.
    """

    statement = select(HabitCompletion.completion_date).where(
        HabitCompletion.habit_id == habit.id)
    existing_dates = set(session.exec(statement).all())

    new_completions = []

    for completion_date in set(bulk_in.dates):
        if completion_date not in existing_dates:
            new_completions.append(
                HabitCompletion(
                    habit_id=habit.id,
                    completion_date=completion_date
                )
            )

    if not new_completions:
        return BulkResponse(entries_created=0)

    session.add_all(new_completions)
    session.commit()

    return BulkResponse(entries_created=len(new_completions))
