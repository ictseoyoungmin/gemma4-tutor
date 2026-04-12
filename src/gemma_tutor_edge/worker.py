from __future__ import annotations

import argparse
import asyncio
import logging

from .config import get_settings
from .jobs import process_job
from .llm import build_model
from .storage import SqliteStore


async def worker_loop(poll_interval: float = 2.0, max_jobs: int | None = None) -> None:
    settings = get_settings()
    store = SqliteStore(settings.app_db_path)
    await store.init()
    model = build_model(settings)

    processed = 0
    while True:
        job = await store.fetch_next_job()
        if job is None:
            if max_jobs is not None and processed >= max_jobs:
                return
            await asyncio.sleep(poll_interval)
            continue

        logging.info("Processing job_id=%s type=%s", job.job_id, job.job_type)
        await store.update_job_status(job.job_id, "running")
        try:
            result = await process_job(store=store, model=model, job=job)
            await store.update_job_status(job.job_id, "done", result=result)
        except Exception as exc:  # noqa: BLE001
            await store.update_job_status(job.job_id, "failed", result={"error": str(exc)})
            logging.exception("Job failed: %s", job.job_id)
        processed += 1
        if max_jobs is not None and processed >= max_jobs:
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Gemma Tutor Edge background worker")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--max-jobs", type=int, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    asyncio.run(worker_loop(poll_interval=args.poll_interval, max_jobs=args.max_jobs))


if __name__ == "__main__":
    main()
