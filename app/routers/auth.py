"""Auth endpoints: login, validate, me, register."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_token, decode_token, get_current_user, hash_password, verify_password
from ..config import settings
from ..database import get_db
from ..models import User, UserAgentGrant
from ..schemas import TokenResponse, UserOut, ValidateResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

_bearer = HTTPBearer(auto_error=False)


class LoginBody(BaseModel):
    username: str
    password: str


class RegisterBody(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    """Public self-registration — creates a 'free' role human user."""
    if len(body.username) < 3:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Username must be at least 3 characters")
    if len(body.password) < 8:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Password must be at least 8 characters")

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role="free",
        principal_type="human",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Auto-grant default agents (e.g. Charon) to every new user
    for agent_id in [a.strip() for a in settings.default_agent_ids.split(",") if a.strip()]:
        db.add(UserAgentGrant(user_id=user.id, agent_id=agent_id))
    await db.commit()

    return TokenResponse(
        access_token=create_token(user),
        user_id=user.id,
        username=user.username,
        role=user.role,
        principal_type=user.principal_type,
    )


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
        principal_type=user.principal_type,
    )


@router.get("/validate", response_model=ValidateResponse)
async def validate_token(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by other services to verify a JWT or API key and get principal identity.
    Returns valid=false on any error rather than raising — callers decide how to handle.
    Accepts both short-lived JWTs (humans) and long-lived API keys (agents).
    """
    if not creds:
        return ValidateResponse(valid=False)

    token = creds.credentials

    # Try JWT first (stateless, fast)
    try:
        payload = decode_token(token)
        role = payload["role"]
        return ValidateResponse(
            valid=True,
            user_id=int(payload["sub"]),
            username=payload["username"],
            display_name=payload.get("display_name"),
            role=role,
            principal_type=payload.get("principal_type", "human"),
            is_admin=(role == "admin"),
        )
    except (JWTError, KeyError, ValueError):
        pass

    # Try API key (DB lookup — used by agents)
    try:
        result = await db.execute(
            select(User).where(User.api_key == token, User.is_active == True)  # noqa: E712
        )
        user = result.scalar_one_or_none()
        if user:
            return ValidateResponse(
                valid=True,
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                role=user.role,
                principal_type=user.principal_type,
                is_admin=(user.role == "admin"),
            )
    except Exception:
        pass

    return ValidateResponse(valid=False)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
