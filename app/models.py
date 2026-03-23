from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id:               Mapped[int]           = mapped_column(primary_key=True, autoincrement=True)
    username:         Mapped[str]           = mapped_column(String(64), unique=True, nullable=False)
    hashed_password:  Mapped[str]           = mapped_column(String(256), nullable=False)
    display_name:     Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role:             Mapped[str]           = mapped_column(String(16), nullable=False, default="free")
    principal_type:   Mapped[str]           = mapped_column(String(16), nullable=False, default="human")
    api_key:          Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    is_active:        Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    created_at:       Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())
    last_login:       Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    agent_grants: Mapped[list["UserAgentGrant"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserAgentGrant(Base):
    """Which AgentManager agents a user has access to."""
    __tablename__ = "user_agent_grants"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:    Mapped[int]      = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id:   Mapped[str]      = mapped_column(String(64), nullable=False)   # AgentManager UUID
    granted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="agent_grants")
