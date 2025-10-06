from datetime import datetime, timedelta, timezone
import os
from fastapi import APIRouter, Depends, HTTPException, status
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from sqlmodel import Session, select

from database import get_session
from models import User
from security import create_access_token, create_jwt_tokens, oauth2_scheme, SECRET_KEY, ALGORITHM
from schemas import TokenRefreshResponse
from jose import jwt, JWTError

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
        "scope": "openid email profile https://www.googleapis.com/auth/calendar",
        "prompt": "consent",
        "access_type": "offline",
    }
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.post("/refresh-token", response_model=TokenRefreshResponse)
def refresh_access_token(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    """
    Recibe un refresh_token y devuelve un nuevo access_token.    
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        user_id = int(user_id_str)

    except JWTError:
        raise credentials_exception

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    new_access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": new_access_token}


@router.get('/login')
async def login_via_google(request: Request):
    """
    Redirect a Google para iniciar sesión.
    """
    redirect_uri = request.url_for("auth_via_google")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )


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

    db_user.google_access_token = token.get('access_token')
    if token.get('refresh_token'):
        db_user.google_refresh_token = token.get('refresh_token')

    expires_in = token.get('expires_in', 0)
    db_user.google_token_expires_at = datetime.now(
        timezone.utc) + timedelta(seconds=expires_in)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    jwt_tokens = create_jwt_tokens(user_id=db_user.id)

    return jwt_tokens
