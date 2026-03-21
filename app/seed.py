"""Seed the admin user on first run if no users exist."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import hash_password
from .config import settings
from .database import AsyncSessionLocal
from .models import User


async def seed_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == settings.admin_username))
        if result.scalar_one_or_none():
            return
        admin = User(
            username=settings.admin_username,
            hashed_password=hash_password(settings.admin_password),
            display_name="Administrator",
            role="admin",
        )
        db.add(admin)
        await db.commit()
