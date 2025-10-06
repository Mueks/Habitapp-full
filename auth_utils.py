from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from jose import JWTError, jwt

from database import get_session
from models import User
from security import SECRET_KEY, ALGORITHM, oauth2_scheme, TokenData


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)) -> User:
    """
    Decodifica el token JWT para obtener el ID del usuario, luego busca
    al usuario en la base de datos y lo devuelve.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        token_data = TokenData(user_id=int(user_id_str))
    except JWTError:
        raise credentials_exception

    if token_data.user_id is None:
        raise credentials_exception

    user = db.get(User, token_data.user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    return user
