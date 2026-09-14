"""
Authentication API routes with 2FA / TOTP support.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    TwoFactorLoginRequest,
    TwoFactorEnableRequest,
    TwoFactorDisableRequest,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_temp_2fa_token,
    decode_token,
    get_user_by_id,
    verify_password,
)
from app.services.totp_service import totp_service
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens or 2FA challenge."""
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if 2FA is enforced
    if user.totp_enabled:
        temp_token = create_temp_2fa_token(user)
        return TokenResponse(
            access_token="",
            refresh_token="",
            expires_in=300,
            require_2fa=True,
            temp_token=temp_token,
        )

    user.last_login = datetime.utcnow()
    await db.commit()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        require_2fa=False,
    )


@router.post("/login/2fa", response_model=TokenResponse)
async def login_2fa(request: TwoFactorLoginRequest, db: AsyncSession = Depends(get_db)):
    """Complete login challenge with 6-digit TOTP code."""
    payload = decode_token(request.temp_token)
    if not payload or payload.get("type") != "2fa_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired 2FA session. Please sign in again.",
        )

    user_id = int(payload.get("sub", 0))
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or 2FA not properly configured.",
        )

    if not totp_service.verify_code(user.totp_secret, request.code.strip()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 6-digit verification code.",
        )

    user.last_login = datetime.utcnow()
    await db.commit()

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        require_2fa=False,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = int(payload.get("sub", 0))
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    access_token = create_access_token(user)
    new_refresh = create_refresh_token(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "totp_enabled": user.totp_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.post("/2fa/setup")
async def setup_2fa(user: User = Depends(get_current_user)):
    """Generate a fresh TOTP secret and QR code for 2FA onboarding."""
    secret = totp_service.generate_secret()
    provisioning_uri = totp_service.get_provisioning_uri(secret, user.username)
    qr_code = totp_service.generate_qr_data_uri(provisioning_uri)

    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code": qr_code,
    }


@router.post("/2fa/enable")
async def enable_2fa(
    request: TwoFactorEnableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm and enable 2FA by verifying the first TOTP code."""
    if not totp_service.verify_code(request.secret.strip(), request.code.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 6-digit code. Please ensure your device clock is synced.",
        )

    user.totp_secret = request.secret.strip()
    user.totp_enabled = True

    log = ActivityLog(
        user_id=user.id,
        action="auth.2fa_enabled",
        category="security",
        description="Enabled two-factor authentication (TOTP)",
        resource_type="user",
        resource_name=user.username,
    )
    db.add(log)
    await db.commit()

    return {"success": True, "message": "Two-factor authentication successfully enabled"}


@router.post("/2fa/disable")
async def disable_2fa(
    request: TwoFactorDisableRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA for the current user."""
    verified = False
    if request.code and user.totp_secret:
        verified = totp_service.verify_code(user.totp_secret, request.code.strip())
    elif request.password:
        verified = verify_password(request.password, user.hashed_password)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code or password",
        )

    user.totp_enabled = False
    user.totp_secret = None

    log = ActivityLog(
        user_id=user.id,
        action="auth.2fa_disabled",
        category="security",
        description="Disabled two-factor authentication (TOTP)",
        resource_type="user",
        resource_name=user.username,
    )
    db.add(log)
    await db.commit()

    return {"success": True, "message": "Two-factor authentication disabled"}
