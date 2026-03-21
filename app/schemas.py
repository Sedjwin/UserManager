from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserOut(BaseModel):
    id:           int
    username:     str
    display_name: Optional[str]
    role:         str
    is_active:    bool
    created_at:   datetime
    last_login:   Optional[datetime]

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username:     str
    password:     str
    display_name: Optional[str] = None
    role:         str = "free"


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    password:     Optional[str] = None
    role:         Optional[str] = None
    is_active:    Optional[bool] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    username:     str
    role:         str


class ValidateResponse(BaseModel):
    valid:        bool
    user_id:      Optional[int] = None
    username:     Optional[str] = None
    display_name: Optional[str] = None
    role:         Optional[str] = None
