from __future__ import annotations

from dataclasses import dataclass

from .storage import SqliteStore


@dataclass
class TutorDeps:
    user_id: str
    store: SqliteStore


@dataclass
class ContentDeps:
    user_id: str
    store: SqliteStore
