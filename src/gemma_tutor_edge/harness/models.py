from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HarnessCase(BaseModel):
    case_id: str
    route: Literal["chat", "quiz_generate"]
    payload: dict
    expect_keys: list[str] = Field(default_factory=list)
    max_latency_ms: int = 20000
