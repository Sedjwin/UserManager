from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]           = mapped_column(primary_key=True, autoincrement=True)
    username:        Mapped[str]           = mapped_column(String(64), unique=True, nullable=False)
    hashed_password: Mapped[str]           = mapped_column(String(256), nullable=False)
    display_name:    Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role:            Mapped[str]           = mapped_column(String(16), nullable=False, default="free")
    is_active:       Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    created_at:      Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())
    last_login:      Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
