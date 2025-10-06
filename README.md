# HabitApp API 🚀

[![Python Version](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

Bienvenido al backend de **HabitApp**, una API robusta y moderna diseñada para construir, rastrear y analizar hábitos. Construida con FastAPI y SQLModel, esta API es rápida, segura y está lista para ser consumida por cualquier frontend (web o móvil).

Hecho con   ❤️   desde Argentina · Código abierto

---

## ✨ Características Principales

-   **Autenticación Segura:** Inicio de sesión con Google (OAuth 2.0) y gestión de sesiones mediante JWT (JSON Web Tokens).
-   **Gestión Completa de Hábitos:** CRUD completo (Crear, Leer, Actualizar, Borrar) para los hábitos de cada usuario.
-   **Tipos de Hábitos Flexibles:** Soporte para diferentes tipos de hábitos:
    -   **Simples:** Tareas de sí/no diarias (ej. "Tender la cama").
    -   **De Frecuencia:** Tareas que se repiten N veces al día (ej. "Tomar 8 vasos de agua").
    -   **De Temporizador:** Tareas medidas por tiempo, ideal para técnicas como Pomodoro (ej. "Estudiar 2 horas").
-   **Seguimiento de Progreso:** Endpoints para registrar y consultar el progreso diario de cada hábito.
-   **Documentación Automática:** Documentación interactiva de la API generada automáticamente por FastAPI, disponible en `/docs`.

## 🛠️ Stack Tecnológico

-   **Backend:** [Python 3.13+](https://www.python.org/)
-   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Base de Datos:** [SQLite](https://www.sqlite.org/index.html) (para desarrollo)
-   **ORM / Validación:** [SQLModel](https://sqlmodel.tiangolo.com/) (combina SQLAlchemy y Pydantic)
-   **Autenticación:**
    -   [Authlib](https://authlib.org/) para el flujo de OAuth 2.0.
    -   [python-jose](https://github.com/mpdavis/python-jose) para la creación y validación de JWT.
-   **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)

## ⚙️ Instalación y Puesta en Marcha

Sigue estos pasos para poner en marcha el servidor de la API en tu entorno local.

### Prerrequisitos

-   Python 3.13 o superior.
-   `git` para clonar el repositorio.

### Pasos

1.  **Clona el repositorio:**
    ```bash
    git clone <URL_DE_TU_REPOSITORIO>
    cd <NOMBRE_DEL_REPOSITORIO>
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    # Crear el entorno
    python -m venv .venv

    # Activar en Linux/macOS
    source .venv/bin/activate

    # Activar en Windows
    .\.venv\Scripts\activate
    ```

3.  **Instala las dependencias:**
    Crea un archivo `requirements.txt` con el siguiente comando y luego instala desde él.
    ```bash
    pip freeze > requirements.txt
    pip install -r requirements.txt
    ```

4.  **Configura las variables de entorno:**
    Crea un archivo llamado `.env` en la raíz del proyecto. Copia el contenido de `.env.example` y rellena tus propios valores.
    
    **.env.example**
    ```env
    # Clave secreta para firmar JWTs y sesiones. Genera una cadena aleatoria y segura.
    # Puedes usar: openssl rand -hex 32
    SECRET_KEY="tu_super_secreto_aqui"

    # Credenciales de Google Cloud para OAuth 2.0
    GOOGLE_CLIENT_ID="tu_client_id_de_google.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET="tu_client_secret_de_google"

    # (Opcional) URL del frontend para las redirecciones
    FRONTEND_URL="http://localhost:3000"
    ```

5.  **Inicia el servidor:**
    ```bash
    uvicorn main:app --reload
    ```
    El servidor estará disponible en `http://127.0.0.1:8000`. La opción `--reload` reiniciará el servidor automáticamente cada vez que hagas un cambio en el código.

## 🚀 Uso de la API

Una vez que el servidor esté en funcionamiento, puedes interactuar con la API.

### 1. Autenticación

El flujo de autenticación está basado en JWT.

1.  **Iniciar sesión:** Dirige tu navegador (o tu cliente de API) a `GET /auth/login`. Serás redirigido a la página de inicio de sesión de Google.
2.  **Callback:** Después de un inicio de sesión exitoso, Google te redirigirá a `GET /auth/callback`. La respuesta de este endpoint será un JSON con tu `access_token` y `refresh_token`.
    ```json
    {
      "access_token": "ey...",
      "refresh_token": "ey...",
      "token_type": "bearer"
    }
    ```
3.  **Realizar peticiones autorizadas:** Para acceder a las rutas protegidas, incluye el `access_token` en la cabecera `Authorization` de tus peticiones.
    ```
    Authorization: Bearer <tu_access_token>
    ```

### 2. Documentación Interactiva

La forma más fácil de explorar y probar todos los endpoints es a través de la documentación interactiva de Swagger UI, disponible en:

**`http://127.0.0.1:8000/docs`**

Desde allí, puedes autorizar tu sesión usando el token y probar cada endpoint directamente desde el navegador.

## API Endpoints

Aquí hay un resumen de los endpoints disponibles:

### Autenticación (`/auth`)
- `GET /login`: Inicia el flujo de autenticación con Google.
- `GET /callback`: Endpoint de callback para Google. Devuelve los tokens JWT.

### Usuarios (`/users`)
- `GET /`: Devuelve la información del usuario autenticado actualmente.

### Hábitos (`/habits`)
- `POST /`: Crea un nuevo hábito.
- `GET /`: Obtiene la lista de todos los hábitos del usuario.
- `GET /{habit_id}`: Obtiene un hábito específico por su ID.
- `PUT /{habit_id}`: Actualiza un hábito.
- `DELETE /{habit_id}`: Elimina un hábito.

### Seguimiento de Hábitos (`/habits/{habit_id}/...`)
- `POST /complete`: Marca un hábito simple como completado para una fecha.
- `DELETE /complete`: Deshace la acción de completar para una fecha.
- `GET /completions`: Obtiene el historial de completitud de un hábito.
- `POST /track`: Registra progreso para un hábito de frecuencia o temporizador (ej. suma minutos o repeticiones).

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE.md) para más detalles.

