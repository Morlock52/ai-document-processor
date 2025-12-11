from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.app_settings import AppSettings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def get_or_create_app_settings(db: Session) -> AppSettings:
    settings_row = db.query(AppSettings).first()
    if not settings_row:
        settings_row = AppSettings(require_login=False)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def hash_passcode(passcode: str) -> str:
    return pwd_context.hash(passcode)


def verify_passcode(passcode: str, hashed_passcode: str) -> bool:
    return pwd_context.verify(passcode, hashed_passcode)


def update_login_settings(db: Session, require_login: bool, passcode: Optional[str] = None) -> AppSettings:
    settings_row = get_or_create_app_settings(db)

    if passcode:
        settings_row.login_passcode_hash = hash_passcode(passcode)

    if require_login and not settings_row.login_passcode_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passcode must be set before enabling login protection",
        )

    settings_row.require_login = require_login
    settings_row.updated_at = datetime.utcnow()

    db.add(settings_row)
    db.commit()
    db.refresh(settings_row)
    return settings_row


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as exc:  # pragma: no cover - jose already provides detail
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
