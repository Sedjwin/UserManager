"""Internal service-to-service endpoints for managing agent principals.

Only accessible with the correct X-Service-Key header (set in .env as SERVICE_KEY).
Called by AgentManager when agents are created or deleted.
"""
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import PrincipalCreate, PrincipalCreated

router = APIRouter(prefix="/internal", tags=["Internal"])


def _require_service_key(x_service_key: str = Header(...)):
    if x_service_key != settings.service_key:
        raise HTTPException(403, "Invalid service key")


@router.post("/principals", response_model=PrincipalCreated, status_code=201)
async def create_agent_principal(
    body: PrincipalCreate,
    _: str = Depends(_require_service_key),
    db: AsyncSession = Depends(get_db),
):
    """Register a new agent as a principal. Returns the agent's API key."""
    # Idempotent: return existing if already registered
    result = await db.execute(select(User).where(User.username == body.username))
    existing = result.scalar_one_or_none()
    if existing:
        if not existing.api_key:
            existing.api_key = secrets.token_hex(32)
            await db.commit()
            await db.refresh(existing)
        return PrincipalCreated(user_id=existing.id, api_key=existing.api_key)

    api_key = secrets.token_hex(32)
    user = User(
        username=body.username,
        hashed_password="",          # agents never use password login
        display_name=body.display_name,
        role="agent",
        principal_type="agent",
        api_key=api_key,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return PrincipalCreated(user_id=user.id, api_key=user.api_key)


@router.delete("/principals/{user_id}", status_code=204)
async def delete_agent_principal(
    user_id: int,
    _: str = Depends(_require_service_key),
    db: AsyncSession = Depends(get_db),
):
    """Remove an agent's principal record when the agent is deleted."""
    user = await db.get(User, user_id)
    if user and user.principal_type == "agent":
        await db.delete(user)
        await db.commit()
