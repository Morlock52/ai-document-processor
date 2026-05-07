from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PromptVariable(BaseModel):
    name: str
    type: str = "string"
    required: bool = True
    default: Any | None = None
    description: str | None = None


class PromptBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    body: str = ""
    variables: list[PromptVariable] = []
    tags: list[str] = []


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    body: str | None = None
    variables: list[PromptVariable] | None = None
    tags: list[str] | None = None


class PromptOut(PromptBase):
    id: uuid.UUID
    version: int
    created_at: datetime
    updated_at: datetime
