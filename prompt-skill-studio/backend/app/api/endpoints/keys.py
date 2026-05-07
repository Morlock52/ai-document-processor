from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.crypto import fingerprint, wrap
from app.core.db import get_db
from app.core.security import require_session
from app.models.vendor_keys import VendorKey
from app.schemas.keys import KeyCreate, KeyOut

router = APIRouter(prefix="/keys", tags=["keys"], dependencies=[Depends(require_session)])


@router.get("", response_model=list[KeyOut])
def list_keys(db: Session = Depends(get_db)) -> list[KeyOut]:
    rows = db.query(VendorKey).order_by(VendorKey.created_at.desc()).all()
    return [
        KeyOut(
            id=r.id,
            vendor=r.vendor,
            label=r.label,
            fingerprint=r.fingerprint,
            created_at=r.created_at,
            last_used_at=r.last_used_at,
        )
        for r in rows
    ]


@router.post("", response_model=KeyOut, status_code=status.HTTP_201_CREATED)
def create_key(payload: KeyCreate, db: Session = Depends(get_db)) -> KeyOut:
    wrapped = wrap(payload.api_key)
    row = VendorKey(
        vendor=payload.vendor,
        label=payload.label,
        fingerprint=fingerprint(payload.api_key),
        nonce=wrapped.nonce,
        ciphertext=wrapped.ciphertext,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return KeyOut(
        id=row.id,
        vendor=row.vendor,
        label=row.label,
        fingerprint=row.fingerprint,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(key_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    row = db.query(VendorKey).filter(VendorKey.id == key_id).first()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Key not found")
    db.delete(row)
    db.commit()
