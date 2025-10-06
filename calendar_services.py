import httpx
from datetime import date, datetime, timedelta
from models import User, Habit


GOOGLE_CALENDAR_API_URL = "https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest"


async def create_calendar_event_for_habit(user: User, habit: Habit, event_date: date):
    """
    Crea un evento en el calendario principal del usuario para un hábito.

    NOTA: Una implementación de producción necesitaría manejar la renovación
    de tokens usando el refresh_token. Por simplicidad, aquí asumimos
    que el access_token es válido.
    """
    if not user.google_access_token:
        print("El usuario no tiene un token de acceso de Google.")
        return

    event_data = {
        "summary": f"Hábito: {habit.name}",
        "description": habit.description or "Completar este hábito.",
        "start": {
            "date": event_date.isoformat(),
        },
        "end": {
            "date": (event_date + timedelta(days=1)).isoformat()
        },
    }

    headers = {
        "Authorization": f"Bearer {user.google_access_token}",
        "Content-Type": "application/json",
    }

    events_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(events_url, json=event_data, headers=headers)

            response.raise_for_status()
            print("Evento creado exitosamente:", response.json())
        except httpx.HTTPStatusError as e:
            print(
                f"Error al crear el evento en Google Calendar: {e.response.text}")
