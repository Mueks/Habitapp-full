from fastapi import APIRouter, Depends
from models import User
from auth_utils import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=User)
async def get_user(current_user: User = Depends(get_current_user)):
    """
    Obtiene los datos del usuario que ha iniciado sesión.
    Esta ruta está protegida. Si intentas acceder sin iniciar sesión,
    recibirás un error 401 Unauthorized.
    """
    return current_user
