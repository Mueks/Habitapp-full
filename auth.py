import os
from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlmodel import Session, select

from database import get_session
from models import User
from security import create_jwt_tokens

from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    }
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get('/login')
async def login_via_google(request: Request):
    """
    Redirect a Google para iniciar sesión.
    """
    redirect_uri = request.url_for("auth_via_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_via_google(request: Request, db: Session = Depends(get_session)):
    """
    Callback de Google. Procesa la info del usuario, lo crea/actualiza en la BD
    y devuelve los tokens JWT de acceso y refresco.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No se pudo obtener el token de acceso: {err}",
        )

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo obtener la información del usuario desde Google.",
        )

    email = user_info.get('email')
    statement = select(User).where(User.email == email)
    db_user = db.exec(statement).first()

    if not db_user:
        new_user = User(
            google_id=user_info.get("sub"),
            email=email,
            full_name=user_info.get('name'),
            picture_url=user_info.get('picture'),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = new_user
    else:
        db_user.full_name = user_info.get('name')
        db_user.picture_url = user_info.get('picture')
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    jwt_tokens = create_jwt_tokens(user_id=db_user.id)

    # El frontend recibirá este JSON y deberá guardar los tokens.
    return jwt_tokens
