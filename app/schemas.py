from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserOut(BaseModel):
    id:             int
    username:       str
    display_name:   Optional[str]
    role:           str
    principal_type: str
    is_active:      bool
    created_at:     datetime
    last_login:     Optional[datetime]

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
    access_token:   str
    token_type:     str = "bearer"
    user_id:        int
    username:       str
    role:           str
    principal_type: str


class ValidateResponse(BaseModel):
    valid:          bool
    user_id:        Optional[int] = None
    username:       Optional[str] = None
    display_name:   Optional[str] = None
    role:           Optional[str] = None
    principal_type: Optional[str] = None
    is_admin:       bool = False


# Used by AgentManager via the internal endpoint
class PrincipalCreate(BaseModel):
    username:     str   # e.g. "agent_<uuid>"
    display_name: str   # agent's human-readable name


class PrincipalCreated(BaseModel):
    user_id: int
    api_key: str
