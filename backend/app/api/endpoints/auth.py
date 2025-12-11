from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import AuthStatus, LoginRequest, LoginResponse, LoginSettingsUpdate
from app.services.auth_settings import (
    create_access_token,
    get_or_create_app_settings,
    update_login_settings,
    verify_passcode,
)

router = APIRouter()


@router.get("/status", response_model=AuthStatus)
def get_auth_status(db: Session = Depends(get_db)):
    settings_row = get_or_create_app_settings(db)
    return AuthStatus(
        require_login=settings_row.require_login,
        login_configured=bool(settings_row.login_passcode_hash),
    )


@router.put("/settings/login", response_model=AuthStatus)
def toggle_login_settings(update: LoginSettingsUpdate, db: Session = Depends(get_db)):
    if update.require_login and not update.passcode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set a passcode before enabling login",
        )

    settings_row = update_login_settings(
        db,
        require_login=update.require_login,
        passcode=update.passcode,
    )

    return AuthStatus(
        require_login=settings_row.require_login,
        login_configured=bool(settings_row.login_passcode_hash),
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    settings_row = get_or_create_app_settings(db)

    if not settings_row.login_passcode_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login protection has not been configured yet",
        )

    if not verify_passcode(request.passcode, settings_row.login_passcode_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passcode",
        )

    token = create_access_token("app-user")
    return LoginResponse(access_token=token)
