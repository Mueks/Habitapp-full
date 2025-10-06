from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import date

from database import get_session
from models import User, Habit, HabitCompletion
from auth_utils import get_current_user
from schemas import HabitCompletionCreate, HabitCreate, HabitRead, HabitUpdate, HabitCompletionRead, HabitTrack

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
def create_habit(
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


@router.put("/{habit_id}", response_model=HabitRead)
def update_habit_by_id(
    *,
    session: Session = Depends(get_session),
    habit_in: HabitUpdate,
    habit: Habit = Depends(get_valid_habit_for_user)
):
    """Actualiza un hábito por su ID usando la dependencia."""
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
    # Reutilizamos nuestra dependencia
    habit: Habit = Depends(get_valid_habit_for_user),
    completion_in: HabitCompletionCreate
):
    """
    Marca un hábito como completado para una fecha específica (por defecto, hoy).
    Evita que se marque como completado dos veces en el mismo día.
    """
    # Si el frontend no especifica una fecha, usamos la de hoy.
    completion_date = completion_in.completion_date or date.today()

    # Verificación: ¿Ya está completado para esta fecha?
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

    # Creamos el nuevo registro de completitud.
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
    completion_date: date | None = None  # Recibimos la fecha como un query parameter
):
    """
    Elimina el registro de completitud de un hábito para una fecha específica (por defecto, hoy).
    """
    target_date = completion_date or date.today()

    # Buscamos el registro de completitud que coincida.
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
    # Gracias a la relación que definimos en el modelo,
    # simplemente podemos acceder a habit.completions.
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

    # Buscar si ya existe un registro de completitud para este hábito hoy.
    statement = select(HabitCompletion).where(
        HabitCompletion.habit_id == habit.id,
        HabitCompletion.completion_date == today
    )
    db_completion = session.exec(statement).first()

    if db_completion:
        # Si existe, le sumamos el nuevo valor.
        # Usamos `or 0` por si el valor era None.
        db_completion.value = (db_completion.value or 0) + track_in.value
    else:
        # Si no existe, creamos un nuevo registro.
        db_completion = HabitCompletion(
            habit_id=habit.id,
            completion_date=today,
            value=track_in.value
        )

    session.add(db_completion)
    session.commit()
    session.refresh(db_completion)

    return db_completion
