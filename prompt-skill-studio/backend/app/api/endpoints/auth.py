from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import (
    cookie_kwargs,
    hash_passcode,
    issue_session_cookie,
    require_session,
    verify_passcode,
    verify_session_cookie,
)
from app.models.app_settings import AppSettings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    passcode: str


class StatusResponse(BaseModel):
    require_login: bool
    authenticated: bool


def _resolve_settings(db: Session) -> AppSettings:
    row = db.query(AppSettings).first()
    if row is None:
        # Bootstrap from env passcode on first call.
        s = get_settings()
        row = AppSettings(
            require_login=bool(s.studio_passcode),
            login_passcode_hash=hash_passcode(s.studio_passcode) if s.studio_passcode else None,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/status", response_model=StatusResponse)
def status_(
    studio_session: str | None = Cookie(default=None, alias=get_settings().session_cookie_name),
    db: Session = Depends(get_db),
) -> StatusResponse:
    row = _resolve_settings(db)
    authed = False
    if studio_session:
        try:
            verify_session_cookie(studio_session)
            authed = True
        except HTTPException:
            authed = False
    return StatusResponse(require_login=row.require_login, authenticated=authed)


@router.post("/login")
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)) -> dict:
    row = _resolve_settings(db)
    if not row.require_login:
        token = issue_session_cookie()
        response.set_cookie(value=token, **cookie_kwargs())
        return {"ok": True, "bypass": True}
    if not row.login_passcode_hash or not verify_passcode(payload.passcode, row.login_passcode_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid passcode")
    token = issue_session_cookie()
    response.set_cookie(value=token, **cookie_kwargs())
    return {"ok": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me")
def me(_: str = Depends(require_session)) -> dict:
    return {"subject": "studio"}
