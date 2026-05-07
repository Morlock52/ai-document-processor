"""Run endpoint — streaming via Server-Sent Events.

M1 ships a stub adapter that emits a deterministic token sequence so the
front-end playground can be wired and tested end-to-end. M2 swaps in the real
Anthropic / OpenAI adapters in `services/vendors/{anthropic,openai}.py`.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, get_db
from app.core.security import require_session
from app.models.artifacts import ArtifactType, Prompt, Run, RunStatus
from app.models.vendor_keys import Vendor

router = APIRouter(prefix="/runs", tags=["runs"], dependencies=[Depends(require_session)])


class RunRequest(BaseModel):
    artifact_type: ArtifactType = ArtifactType.prompt
    artifact_id: uuid.UUID | None = None
    vendor: Vendor
    model: str
    system: str | None = None
    user: str | None = None
    variables: dict = {}
    max_tokens: int = 1024


def _hydrate(prompt_body: str, variables: dict) -> str:
    out = prompt_body
    for k, v in (variables or {}).items():
        out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def _resolve_input(payload: RunRequest, db: Session) -> tuple[str | None, str]:
    if payload.artifact_type == ArtifactType.prompt and payload.artifact_id:
        p = db.query(Prompt).filter(Prompt.id == payload.artifact_id).first()
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        return payload.system, _hydrate(p.body, payload.variables)
    if payload.user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="user or artifact_id required")
    return payload.system, _hydrate(payload.user, payload.variables)


async def _stub_stream(model: str, user: str) -> AsyncIterator[dict]:
    """Until M2 wires real SDKs, this emits a labelled echo so the UI is testable."""
    preamble = f"[stub:{model}] "
    body = f"You said: {user[:240]}"
    text = preamble + body
    for ch in text:
        await asyncio.sleep(0.01)
        yield {"event": "token", "data": ch}
    yield {
        "event": "usage",
        "data": {"input_tokens": len(user) // 4, "output_tokens": len(text) // 4},
    }
    yield {"event": "done", "data": {"finish_reason": "stop"}}


def _sse(frame: dict) -> bytes:
    payload = json.dumps(frame["data"], ensure_ascii=False)
    return f"event: {frame['event']}\ndata: {payload}\n\n".encode("utf-8")


@router.post("")
async def create_run(payload: RunRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    system, user_text = _resolve_input(payload, db)

    run = Run(
        artifact_type=payload.artifact_type,
        artifact_id=payload.artifact_id,
        vendor=payload.vendor,
        model=payload.model,
        input={"system": system, "user": user_text, "variables": payload.variables},
        status=RunStatus.streaming,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    run_id = run.id

    async def gen() -> AsyncIterator[bytes]:
        # Emit run id first so the client can attach it to UI state.
        yield _sse({"event": "run", "data": {"id": str(run_id)}})
        collected = []
        usage: dict = {}
        try:
            async for frame in _stub_stream(payload.model, user_text):
                if frame["event"] == "token":
                    collected.append(frame["data"])
                elif frame["event"] == "usage":
                    usage = frame["data"]
                yield _sse(frame)
        except Exception as exc:  # pragma: no cover
            yield _sse({"event": "error", "data": {"message": str(exc)}})
            with SessionLocal() as s:
                row = s.get(Run, run_id)
                if row:
                    row.status = RunStatus.failed
                    row.error = str(exc)
                    row.completed_at = datetime.now(timezone.utc)
                    s.commit()
            return

        finished = datetime.now(timezone.utc)
        with SessionLocal() as s:
            row = s.get(Run, run_id)
            if row:
                row.output = "".join(collected)
                row.usage = usage
                row.status = RunStatus.completed
                row.completed_at = finished
                row.latency_ms = int(
                    (finished - (row.started_at or finished)).total_seconds() * 1000
                )
                s.commit()

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{run_id}")
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    row = db.get(Run, run_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Run not found")
    return {
        "id": str(row.id),
        "status": row.status.value,
        "vendor": row.vendor.value,
        "model": row.model,
        "output": row.output,
        "usage": row.usage,
        "latency_ms": row.latency_ms,
        "error": row.error,
    }
