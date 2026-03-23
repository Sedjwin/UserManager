"""Agent grant management — which agents each user can access.

GET  /users/me/agents             — current user's granted agent IDs
GET  /users/{id}/agents           — admin: any user's granted agent IDs
POST /users/{id}/agents           — admin: grant an agent to a user
DELETE /users/{id}/agents/{agent} — admin: revoke an agent from a user
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import User, UserAgentGrant

router = APIRouter(tags=["Agent Grants"])

_admin = require_role("admin")


class GrantBody(BaseModel):
    agent_id: str


@router.get("/users/me/agents", response_model=list[str])
async def my_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the list of AgentManager agent UUIDs this user has access to."""
    result = await db.execute(
        select(UserAgentGrant.agent_id).where(UserAgentGrant.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/users/{user_id}/agents", response_model=list[str])
async def user_agents(
    user_id: int,
    _: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAgentGrant.agent_id).where(UserAgentGrant.user_id == user_id)
    )
    return result.scalars().all()


@router.post("/users/{user_id}/agents", status_code=201)
async def grant_agent(
    user_id: int,
    body: GrantBody,
    _: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    existing = await db.execute(
        select(UserAgentGrant).where(
            UserAgentGrant.user_id == user_id,
            UserAgentGrant.agent_id == body.agent_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"detail": "already granted"}

    db.add(UserAgentGrant(user_id=user_id, agent_id=body.agent_id))
    await db.commit()
    return {"detail": "granted"}


@router.delete("/users/{user_id}/agents/{agent_id}", status_code=204)
async def revoke_agent(
    user_id: int,
    agent_id: str,
    _: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserAgentGrant).where(
            UserAgentGrant.user_id == user_id,
            UserAgentGrant.agent_id == agent_id,
        )
    )
    grant = result.scalar_one_or_none()
    if not grant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Grant not found")
    await db.delete(grant)
    await db.commit()
