"""User CRUD — admin-only except /users/me and self password change."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, hash_password, require_role
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

_admin = require_role("admin")


@router.get("", response_model=list[UserOut])
async def list_users(
    _: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    _: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Username already taken")

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        display_name=body.display_name,
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    caller: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if caller.role != "admin" and caller.id != user_id:
        raise HTTPException(403, "Forbidden")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    caller: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_admin = caller.role == "admin"
    is_self  = caller.id == user_id

    if not is_admin and not is_self:
        raise HTTPException(403, "Forbidden")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.password is not None:
        user.hashed_password = hash_password(body.password)
    if body.role is not None:
        if not is_admin:
            raise HTTPException(403, "Only admins can change roles")
        user.role = body.role
    if body.is_active is not None:
        if not is_admin:
            raise HTTPException(403, "Only admins can activate/deactivate users")
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    caller: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
):
    if caller.id == user_id:
        raise HTTPException(400, "Cannot delete your own account")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    await db.delete(user)
    await db.commit()
