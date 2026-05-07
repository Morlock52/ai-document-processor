from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_session
from app.models.artifacts import Prompt
from app.schemas.prompts import PromptCreate, PromptOut, PromptUpdate

router = APIRouter(prefix="/prompts", tags=["prompts"], dependencies=[Depends(require_session)])


def _to_out(p: Prompt) -> PromptOut:
    return PromptOut.model_validate(
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "body": p.body,
            "variables": p.variables or [],
            "tags": p.tags or [],
            "version": p.version,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
    )


@router.get("", response_model=list[PromptOut])
def list_prompts(db: Session = Depends(get_db)) -> list[PromptOut]:
    rows = db.query(Prompt).order_by(Prompt.updated_at.desc()).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=PromptOut, status_code=status.HTTP_201_CREATED)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)) -> PromptOut:
    row = Prompt(
        name=payload.name,
        description=payload.description,
        body=payload.body,
        variables=[v.model_dump() for v in payload.variables],
        tags=payload.tags,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.get("/{prompt_id}", response_model=PromptOut)
def get_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)) -> PromptOut:
    row = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    return _to_out(row)


@router.patch("/{prompt_id}", response_model=PromptOut)
def update_prompt(
    prompt_id: uuid.UUID, payload: PromptUpdate, db: Session = Depends(get_db)
) -> PromptOut:
    row = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    if payload.name is not None:
        row.name = payload.name
    if payload.description is not None:
        row.description = payload.description
    if payload.body is not None:
        row.body = payload.body
        row.version += 1
    if payload.variables is not None:
        row.variables = [v.model_dump() for v in payload.variables]
    if payload.tags is not None:
        row.tags = payload.tags
    db.commit()
    db.refresh(row)
    return _to_out(row)


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(prompt_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    row = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Prompt not found")
    db.delete(row)
    db.commit()
