"""Token Models."""
from typing import Optional

from pydantic import BaseModel

from app.api.database.models.user import UserSchema


class Token(BaseModel):
    """Token Model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token Data."""
    username: Optional[str] = None


class UserInDB(UserSchema):
    """User In DB."""
    hashed_password: str
