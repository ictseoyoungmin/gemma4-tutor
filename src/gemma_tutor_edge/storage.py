from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic_ai import ModelMessage, ModelMessagesTypeAdapter

from .schemas import (
    AchievementCard,
    BackgroundJob,
    ChatSessionMeta,
    DashboardDetail,
    DashboardOverview,
    MemoryItem,
    PackGenerationMeta,
    PracticeItemDetail,
    ProblemInventoryResponse,
    ProblemStats,
    PracticeItemSummary,
    QuizPack,
    ReadyPackDetail,
    ReadyQuizSummary,
    SkillSnapshot,
    ToeicPracticeItem,
)


class SqliteStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS quizzes (
                    quiz_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    quiz_id TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    score REAL NOT NULL,
                    feedback_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS background_jobs (
                    job_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS ready_packs (
                    ready_pack_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    generation_json TEXT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor = await db.execute("PRAGMA table_info(ready_packs)")
            ready_pack_columns = {row[1] for row in await cursor.fetchall()}
            if "generation_json" not in ready_pack_columns:
                await db.execute("ALTER TABLE ready_packs ADD COLUMN generation_json TEXT NULL")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS skill_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    score REAL NOT NULL,
                    delta REAL NOT NULL,
                    evidence_count INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    unlocked INTEGER NOT NULL,
                    unlocked_at TEXT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS toeic_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    part_type TEXT NOT NULL,
                    difficulty_level TEXT NOT NULL,
                    grammar_tag TEXT NOT NULL,
                    vocab_tag TEXT NULL,
                    selected_option TEXT NOT NULL,
                    correct INTEGER NOT NULL,
                    response_time_ms INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS practice_items (
                    item_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    part_type TEXT NOT NULL,
                    difficulty_level TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    grammar_tag TEXT NOT NULL,
                    vocab_tag TEXT NULL,
                    payload_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    messages_json TEXT NOT NULL,
                    backend TEXT NULL,
                    model_name TEXT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor = await db.execute("PRAGMA table_info(chat_sessions)")
            chat_session_columns = {row[1] for row in await cursor.fetchall()}
            if "backend" not in chat_session_columns:
                await db.execute("ALTER TABLE chat_sessions ADD COLUMN backend TEXT NULL")
            if "model_name" not in chat_session_columns:
                await db.execute("ALTER TABLE chat_sessions ADD COLUMN model_name TEXT NULL")
            await db.commit()

    async def seed_placeholders(self, user_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT COUNT(*) FROM achievements WHERE user_id = ?",
                (user_id,),
            )
            achievement_count = (await cur.fetchone())[0]
            if achievement_count == 0:
                for achievement in [
                    AchievementCard(title="First Conversation", description="Start your first tutor chat."),
                    AchievementCard(title="Warm Streak", description="Study 3 days in a row."),
                    AchievementCard(title="Image Learner", description="Complete one image-based lesson."),
                ]:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO achievements(
                            achievement_id, user_id, title, description, unlocked, unlocked_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            achievement.achievement_id,
                            user_id,
                            achievement.title,
                            achievement.description,
                            int(achievement.unlocked),
                            achievement.unlocked_at.isoformat() if achievement.unlocked_at else None,
                        ),
                    )
            cur = await db.execute(
                "SELECT COUNT(*) FROM skill_snapshots WHERE user_id = ?",
                (user_id,),
            )
            snapshot_count = (await cur.fetchone())[0]
            if snapshot_count == 0:
                for skill_name, score, delta in [
                    ("grammar", 0.42, 0.08),
                    ("toeic_reading", 0.51, 0.04),
                    ("conversation", 0.36, 0.11),
                    ("idioms", 0.28, 0.02),
                ]:
                    await db.execute(
                        """
                        INSERT INTO skill_snapshots(user_id, skill_name, score, delta, evidence_count)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (user_id, skill_name, score, delta, 3),
                    )
            await db.commit()

    async def add_memory(self, user_id: str, item: MemoryItem) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO memories(memory_id, user_id, category, content, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item.memory_id,
                    user_id,
                    item.category,
                    item.content,
                    item.confidence,
                    item.created_at.isoformat(),
                ),
            )
            await db.commit()

    async def list_recent_memories(self, user_id: str, limit: int = 5) -> list[MemoryItem]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT memory_id, category, content, confidence, created_at
                FROM memories
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            MemoryItem(
                memory_id=row[0],
                category=row[1],
                content=row[2],
                confidence=row[3],
                created_at=row[4],
            )
            for row in rows
        ]

    async def load_chat_history(self, user_id: str, session_id: str) -> list[ModelMessage]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT messages_json
                FROM chat_sessions
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id),
            )
            row = await cursor.fetchone()
        if row is None or not row[0]:
            return []
        try:
            return ModelMessagesTypeAdapter.validate_json(row[0])
        except Exception:  # noqa: BLE001
            return []

    async def load_raw_chat_messages(
        self,
        user_id: str,
        session_id: str,
        *,
        limit: int = 8,
    ) -> list[dict[str, str]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT messages_json
                FROM chat_sessions
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id),
            )
            row = await cursor.fetchone()
        if row is None or not row[0]:
            return []
        try:
            messages = json.loads(row[0])
        except json.JSONDecodeError:
            return []
        if not isinstance(messages, list):
            return []
        raw_messages = [
            item
            for item in messages
            if isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and isinstance(item.get("content"), str)
        ]
        return raw_messages[-limit:]

    async def save_raw_chat_messages(
        self,
        user_id: str,
        session_id: str,
        messages: list[dict[str, str]],
        *,
        backend: str | None = None,
        model_name: str | None = None,
    ) -> None:
        await self.save_chat_history(
            user_id,
            session_id,
            json.dumps(messages, ensure_ascii=False),
            backend=backend,
            model_name=model_name,
        )

    async def get_chat_session_meta(self, user_id: str, session_id: str) -> ChatSessionMeta | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT session_id, user_id, backend, model_name, updated_at
                FROM chat_sessions
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return ChatSessionMeta(
            session_id=row[0],
            user_id=row[1],
            backend=row[2],
            model_name=row[3],
            updated_at=row[4],
        )

    async def reset_chat_session(self, user_id: str, session_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM chat_sessions
                WHERE user_id = ? AND session_id = ?
                """,
                (user_id, session_id),
            )
            await db.commit()

    async def save_chat_history(
        self,
        user_id: str,
        session_id: str,
        messages_json: bytes | str,
        *,
        backend: str | None = None,
        model_name: str | None = None,
    ) -> None:
        payload = messages_json.decode("utf-8") if isinstance(messages_json, bytes) else messages_json
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO chat_sessions(
                    session_id, user_id, messages_json, backend, model_name, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    payload,
                    backend,
                    model_name,
                    datetime.utcnow().isoformat(),
                ),
            )
            await db.commit()

    async def save_quiz_pack(self, user_id: str, quiz_id: str, pack: QuizPack) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO quizzes(quiz_id, user_id, title, payload_json)
                VALUES (?, ?, ?, ?)
                """,
                (quiz_id, user_id, pack.title, pack.model_dump_json()),
            )
            await db.commit()

    async def get_quiz_pack(self, quiz_id: str) -> QuizPack | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT payload_json FROM quizzes WHERE quiz_id = ?",
                (quiz_id,),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return QuizPack.model_validate_json(row[0])

    async def save_ready_pack(
        self,
        user_id: str,
        ready_pack_id: str,
        pack: QuizPack,
        created_at: str,
        generation_meta: dict[str, Any] | None = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO ready_packs(
                    ready_pack_id, user_id, title, mode, difficulty, payload_json, generation_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ready_pack_id,
                    user_id,
                    pack.title,
                    pack.mode,
                    pack.difficulty,
                    pack.model_dump_json(),
                    json.dumps(generation_meta, ensure_ascii=False) if generation_meta is not None else None,
                    created_at,
                ),
            )
            await db.commit()

    async def list_ready_packs(self, user_id: str, limit: int = 10) -> list[ReadyQuizSummary]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT ready_pack_id, title, mode, difficulty, generation_json, created_at
                FROM ready_packs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            ReadyQuizSummary(
                ready_pack_id=row[0],
                title=row[1],
                mode=row[2],
                difficulty=row[3],
                generation=PackGenerationMeta.model_validate_json(row[4]) if row[4] else None,
                created_at=row[5],
            )
            for row in rows
        ]

    async def list_ready_packs_page(self, user_id: str, *, page: int = 1, page_size: int = 5) -> list[ReadyQuizSummary]:
        offset = max(page - 1, 0) * page_size
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT ready_pack_id, title, mode, difficulty, generation_json, created_at
                FROM ready_packs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, page_size, offset),
            )
            rows = await cursor.fetchall()
        return [
            ReadyQuizSummary(
                ready_pack_id=row[0],
                title=row[1],
                mode=row[2],
                difficulty=row[3],
                generation=PackGenerationMeta.model_validate_json(row[4]) if row[4] else None,
                created_at=row[5],
            )
            for row in rows
        ]

    async def get_ready_pack(self, user_id: str, ready_pack_id: str) -> ReadyPackDetail | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT payload_json, generation_json
                FROM ready_packs
                WHERE user_id = ? AND ready_pack_id = ?
                """,
                (user_id, ready_pack_id),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return ReadyPackDetail(
            ready_pack_id=ready_pack_id,
            pack=QuizPack.model_validate_json(row[0]),
            generation=PackGenerationMeta.model_validate_json(row[1]) if row[1] else None,
        )

    async def delete_ready_pack(self, user_id: str, ready_pack_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM ready_packs WHERE user_id = ? AND ready_pack_id = ?",
                (user_id, ready_pack_id),
            )
            await db.commit()
        return cursor.rowcount > 0

    async def save_attempt(
        self,
        user_id: str,
        quiz_id: str,
        total: int,
        correct: int,
        score: float,
        feedback: list[str],
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO attempts(user_id, quiz_id, total, correct, score, feedback_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, quiz_id, total, correct, score, json.dumps(feedback)),
            )
            await db.commit()

    async def save_toeic_attempt(
        self,
        *,
        user_id: str,
        item: ToeicPracticeItem,
        selected_option: str,
        correct: bool,
        response_time_ms: int,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO toeic_attempts(
                    user_id, item_id, part_type, difficulty_level, grammar_tag, vocab_tag,
                    selected_option, correct, response_time_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    item.item_id,
                    item.part_type,
                    item.difficulty_level,
                    item.grammar_tag,
                    item.vocab_tag,
                    selected_option,
                    int(correct),
                    response_time_ms,
                ),
            )
            await db.commit()

    async def save_practice_item(
        self,
        *,
        user_id: str,
        item: ToeicPracticeItem,
        source: str,
        created_at: str,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO practice_items(
                    item_id, user_id, part_type, difficulty_level, prompt, question_text,
                    grammar_tag, vocab_tag, payload_json, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.item_id,
                    user_id,
                    item.part_type,
                    item.difficulty_level,
                    item.prompt,
                    item.question_text,
                    item.grammar_tag,
                    item.vocab_tag,
                    item.model_dump_json(),
                    source,
                    created_at,
                ),
            )
            await db.commit()

    async def list_practice_items(self, user_id: str, *, part_type: str | None = None, limit: int = 100) -> list[ToeicPracticeItem]:
        query = """
            SELECT payload_json
            FROM practice_items
            WHERE user_id = ?
        """
        params: list[Any] = [user_id]
        if part_type is not None:
            query += " AND part_type = ?"
            params.append(part_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()
        return [ToeicPracticeItem.model_validate_json(row[0]) for row in rows]

    async def list_practice_item_summaries(
        self,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 5,
    ) -> list[PracticeItemSummary]:
        offset = max(page - 1, 0) * page_size
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT item_id, part_type, difficulty_level, prompt, grammar_tag, vocab_tag, source, created_at
                FROM practice_items
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, page_size, offset),
            )
            rows = await cursor.fetchall()
        return [
            PracticeItemSummary(
                item_id=row[0],
                part_type=row[1],
                difficulty_level=row[2],
                prompt=row[3],
                grammar_tag=row[4],
                vocab_tag=row[5],
                source=row[6],
                created_at=row[7],
            )
            for row in rows
        ]

    async def get_practice_item(self, user_id: str, item_id: str) -> PracticeItemDetail | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT payload_json, source, created_at
                FROM practice_items
                WHERE user_id = ? AND item_id = ?
                """,
                (user_id, item_id),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return PracticeItemDetail(
            item=ToeicPracticeItem.model_validate_json(row[0]),
            source=row[1],
            created_at=row[2],
        )

    async def delete_practice_item(self, user_id: str, item_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM practice_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            await db.commit()
        return cursor.rowcount > 0

    async def list_recent_toeic_attempts(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT item_id, part_type, difficulty_level, grammar_tag, vocab_tag, selected_option, correct,
                       response_time_ms, created_at
                FROM toeic_attempts
                WHERE user_id = ?
                ORDER BY created_at DESC, attempt_id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            {
                "item_id": row[0],
                "part_type": row[1],
                "difficulty_level": row[2],
                "grammar_tag": row[3],
                "vocab_tag": row[4],
                "selected_option": row[5],
                "correct": bool(row[6]),
                "response_time_ms": row[7],
                "created_at": row[8],
            }
            for row in rows
        ]

    async def queue_job(self, job: BackgroundJob) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO background_jobs(
                    job_id, user_id, job_type, status, payload_json, result_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.user_id,
                    job.job_type,
                    job.status,
                    json.dumps(job.payload),
                    json.dumps(job.result),
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )
            await db.commit()

    async def fetch_next_job(self) -> BackgroundJob | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT job_id, user_id, job_type, status, payload_json, result_json, created_at, updated_at
                FROM background_jobs
                WHERE status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return BackgroundJob(
            job_id=row[0],
            user_id=row[1],
            job_type=row[2],
            status=row[3],
            payload=json.loads(row[4]),
            result=json.loads(row[5]),
            created_at=row[6],
            updated_at=row[7],
        )

    async def update_job_status(self, job_id: str, status: str, result: dict[str, Any] | None = None) -> None:
        payload = json.dumps(result or {})
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE background_jobs
                SET status = ?, result_json = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (status, payload, datetime.utcnow().isoformat(), job_id),
            )
            await db.commit()

    async def list_active_jobs(self, user_id: str, limit: int = 20) -> list[BackgroundJob]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT job_id, user_id, job_type, status, payload_json, result_json, created_at, updated_at
                FROM background_jobs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            BackgroundJob(
                job_id=row[0],
                user_id=row[1],
                job_type=row[2],
                status=row[3],
                payload=json.loads(row[4]),
                result=json.loads(row[5]),
                created_at=row[6],
                updated_at=row[7],
            )
            for row in rows
        ]

    async def problem_stats(self, user_id: str) -> ProblemStats:
        async with aiosqlite.connect(self.db_path) as db:
            ready_pack_total = (await (await db.execute(
                "SELECT COUNT(*) FROM ready_packs WHERE user_id = ?", (user_id,)
            )).fetchone())[0]
            practice_total = (await (await db.execute(
                "SELECT COUNT(*) FROM practice_items WHERE user_id = ?", (user_id,)
            )).fetchone())[0]

            cursor = await db.execute(
                """
                SELECT part_type, COUNT(*)
                FROM practice_items
                WHERE user_id = ?
                GROUP BY part_type
                """,
                (user_id,),
            )
            practice_rows = await cursor.fetchall()

            cursor = await db.execute(
                """
                SELECT mode, COUNT(*)
                FROM ready_packs
                WHERE user_id = ?
                GROUP BY mode
                """,
                (user_id,),
            )
            mode_rows = await cursor.fetchall()

        return ProblemStats(
            total_ready_packs=ready_pack_total,
            total_practice_items=practice_total,
            practice_items_by_part={row[0]: row[1] for row in practice_rows},
            ready_packs_by_mode={row[0]: row[1] for row in mode_rows},
        )

    async def problem_inventory(
        self,
        user_id: str,
        *,
        ready_pack_page: int = 1,
        practice_item_page: int = 1,
        page_size: int = 5,
    ) -> ProblemInventoryResponse:
        return ProblemInventoryResponse(
            stats=await self.problem_stats(user_id),
            ready_packs=await self.list_ready_packs_page(user_id, page=ready_pack_page, page_size=page_size),
            practice_items=await self.list_practice_item_summaries(user_id, page=practice_item_page, page_size=page_size),
            active_jobs=await self.list_active_jobs(user_id),
            ready_pack_page=ready_pack_page,
            practice_item_page=practice_item_page,
            page_size=page_size,
        )

    async def dashboard_overview(self, user_id: str) -> DashboardOverview:
        async with aiosqlite.connect(self.db_path) as db:
            memory_count = (await (await db.execute(
                "SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,)
            )).fetchone())[0]
            quiz_count = (await (await db.execute(
                "SELECT COUNT(*) FROM quizzes WHERE user_id = ?", (user_id,)
            )).fetchone())[0]
            attempts_count = (await (await db.execute(
                "SELECT COUNT(*) FROM attempts WHERE user_id = ?", (user_id,)
            )).fetchone())[0]
            avg_row = await (await db.execute(
                "SELECT AVG(score) FROM attempts WHERE user_id = ?", (user_id,)
            )).fetchone()
        avg_score = float(avg_row[0]) if avg_row and avg_row[0] is not None else 0.0
        return DashboardOverview(
            user_id=user_id,
            memory_count=memory_count,
            quiz_count=quiz_count,
            attempts_count=attempts_count,
            average_score=avg_score,
        )

    async def get_skill_snapshots(self, user_id: str, limit: int = 10) -> list[SkillSnapshot]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT skill_name, score, delta, evidence_count
                FROM skill_snapshots
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            SkillSnapshot(skill_name=row[0], score=row[1], delta=row[2], evidence_count=row[3])
            for row in rows
        ]

    async def get_achievements(self, user_id: str, limit: int = 12) -> list[AchievementCard]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT achievement_id, title, description, unlocked, unlocked_at
                FROM achievements
                WHERE user_id = ?
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            AchievementCard(
                achievement_id=row[0],
                title=row[1],
                description=row[2],
                unlocked=bool(row[3]),
                unlocked_at=row[4],
            )
            for row in rows
        ]

    async def dashboard_detail(self, user_id: str) -> DashboardDetail:
        await self.seed_placeholders(user_id)
        overview = await self.dashboard_overview(user_id)
        return DashboardDetail(
            overview=overview,
            skill_snapshots=await self.get_skill_snapshots(user_id),
            achievements=await self.get_achievements(user_id),
            ready_packs=await self.list_ready_packs(user_id),
            active_jobs=await self.list_active_jobs(user_id),
            roadmap_placeholders=[
                "TTS/STT module placeholder",
                "Curriculum KB ingestion placeholder",
                "Long-term memory summarizer placeholder",
                "Llama.cpp system test pipeline placeholder",
            ],
        )
