from auth import router as auth_router
from users import router as users_router
from habits import router as habits_router
from database import create_db_and_tables
import os
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de contexto para la aplicación.
    Se ejecuta al inicio para crear la base de datos y las tablas.
    """
    print("Iniciando aplicación y creando base de datos...")
    create_db_and_tables()
    yield
    # TODO: Añadir limpieza al cerrar la aplicación
    print("Apagando aplicación...")


app = FastAPI(
    title="Mi App de Hábitos",
    description="API para gestionar hábitos, notificaciones y recordatorios.",
    lifespan=lifespan,
    version="0.1.0",
)


origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY")
)


@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la API de la App de Hábitos"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(habits_router)
