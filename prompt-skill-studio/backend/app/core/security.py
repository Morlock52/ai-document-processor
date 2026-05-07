from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Cookie, HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_passcode(passcode: str) -> str:
    return _pwd.hash(passcode)


def verify_passcode(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _signer() -> TimestampSigner:
    return TimestampSigner(get_settings().session_secret, salt="studio-session")


def issue_session_cookie(subject: str = "studio") -> str:
    """Sign the subject so it can ride in a cookie. Refreshable."""
    return _signer().sign(subject.encode("utf-8")).decode("utf-8")


def verify_session_cookie(token: str) -> str:
    s = get_settings()
    try:
        raw = _signer().unsign(token, max_age=s.session_max_age_seconds)
    except SignatureExpired as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Session expired") from exc
    except BadSignature as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc
    return raw.decode("utf-8")


def require_session(
    studio_session: str | None = Cookie(default=None, alias=get_settings().session_cookie_name),
) -> str:
    if not studio_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return verify_session_cookie(studio_session)


def cookie_kwargs() -> dict:
    s = get_settings()
    return {
        "key": s.session_cookie_name,
        "max_age": s.session_max_age_seconds,
        "httponly": True,
        "samesite": "lax",
        "secure": s.frontend_origin.startswith("https://"),
        "path": "/",
    }


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def in_(seconds: int) -> datetime:
    return now_utc() + timedelta(seconds=seconds)
