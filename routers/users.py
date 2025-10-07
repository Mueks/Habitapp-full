from fastapi import APIRouter, Depends
from models.user_models import User
from utils.auth_utils import get_current_user
from schemas.user_schemas import UserUpdate
from database import get_session
from sqlmodel import Session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=User)
async def get_user(current_user: User = Depends(get_current_user)):
    """
    Obtiene los datos del usuario que ha iniciado sesión.
    Esta ruta está protegida. Si intentas acceder sin iniciar sesión,
    recibirás un error 401 Unauthorized.
    """
    return current_user


@router.patch("/", response_model=User)
def update_current_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    user_in: UserUpdate
):
    """
    Permite al usuario autenticado actualizar sus propios datos,
    como el nombre o la zona horaria.
    """
    update_data = user_in.model_dump(exclude_unset=True)

    current_user.sqlmodel_update(update_data)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return current_user
