"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    require_2fa: bool = False
    temp_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TwoFactorLoginRequest(BaseModel):
    temp_token: str
    code: str


class TwoFactorEnableRequest(BaseModel):
    secret: str
    code: str


class TwoFactorDisableRequest(BaseModel):
    code: Optional[str] = None
    password: Optional[str] = None


class TokenPayload(BaseModel):
    sub: int  # user id
    username: str
    role: str
    exp: int
