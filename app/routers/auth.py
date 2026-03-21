"""Auth endpoints: login, validate, me."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_token, decode_token, get_current_user, verify_password
from ..database import get_db
from ..models import User
from ..schemas import TokenResponse, UserOut, ValidateResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

_bearer = HTTPBearer(auto_error=False)


class LoginRequest:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


from pydantic import BaseModel

class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginBody, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=create_token(user),
        user_id=user.id,
        username=user.username,
        role=user.role,
    )


@router.get("/validate", response_model=ValidateResponse)
async def validate_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
):
    """
    Called by other services to verify a JWT and get user identity.
    Returns valid=false on any error rather than raising — callers decide how to handle.
    """
    if not creds:
        return ValidateResponse(valid=False)
    try:
        payload = decode_token(creds.credentials)
        return ValidateResponse(
            valid=True,
            user_id=int(payload["sub"]),
            username=payload["username"],
            display_name=payload.get("display_name"),
            role=payload["role"],
        )
    except (JWTError, KeyError, ValueError):
        return ValidateResponse(valid=False)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
