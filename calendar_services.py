import httpx
from datetime import date, datetime, timedelta
from models.user_models import User
from models.habit_models import Habit


GOOGLE_CALENDAR_API_URL = "https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest"


async def create_calendar_event_for_habit(user: User, habit: Habit, event_date: date):
    """
    Crea un evento en el calendario del usuario.
    - Si el hábito tiene una hora programada, crea un evento de 1 hora en esa hora.
    - Si no, crea un evento de "todo el día".
    """
    if not user.google_access_token:
        print("El usuario no tiene un token de acceso de Google.")
        return

    event_data = {
        "summary": f"Hábito: {habit.name}",
        "description": habit.description or "Completar este hábito.",
    }

    if habit.scheduled_time:
        start_datetime = datetime.combine(event_date, habit.scheduled_time)
        end_datetime = start_datetime + timedelta(hours=1)

        user_timezone = user.timezone or "UTC"

        event_data["start"] = {
            "dateTime": start_datetime.isoformat(),
            "timeZone": user_timezone,
        }
        event_data["end"] = {
            "dateTime": end_datetime.isoformat(),
            "timeZone": user_timezone,
        }
    else:
        event_data["start"] = {"date": event_date.isoformat()}
        event_data["end"] = {
            "date": (event_date + timedelta(days=1)).isoformat()}

    headers = {
        "Authorization": f"Bearer {user.google_access_token}",
        "Content-Type": "application/json",
    }

    events_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(events_url, json=event_data, headers=headers)
            response.raise_for_status()
            print("Evento de calendario creado exitosamente:", response.json())
        except httpx.HTTPStatusError as e:
            print(
                f"Error al crear el evento en Google Calendar: {e.response.text}")
