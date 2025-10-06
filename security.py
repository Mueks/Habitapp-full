import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No se encontró SECRET_KEY en las variables de entorno")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class TokenData(BaseModel):
    user_id: int | None = None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Crea un nuevo token de acceso."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:

        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_jwt_tokens(user_id: int) -> dict[str, str]:
    """
    Genera un par de tokens (acceso y refresco) para un ID de usuario.

    Args:
        user_id: El ID del usuario para el cual se generan los tokens.

    Returns:
        Un diccionario que contiene el 'access_token' y el 'refresh_token'.
    """

    jwt_payload = {"sub": str(user_id)}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=jwt_payload, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_access_token(
        data=jwt_payload, expires_delta=refresh_token_expires
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
