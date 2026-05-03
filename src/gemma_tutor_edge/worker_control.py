from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .schemas import WorkerStatusResponse


class WorkerController:
    def __init__(self, *, project_root: Path, python_executable: str | None = None):
        self.project_root = project_root
        self.python_executable = python_executable or sys.executable
        self.process: subprocess.Popen[str] | None = None
        self.poll_interval: float | None = None
        self.max_jobs: int | None = None
        self.last_exit_code: int | None = None

    def status(self) -> WorkerStatusResponse:
        if self.process is not None:
            exit_code = self.process.poll()
            if exit_code is not None:
                self.last_exit_code = exit_code
                self.process = None
                self.poll_interval = None
                self.max_jobs = None
        return WorkerStatusResponse(
            state="running" if self.process is not None else "stopped",
            pid=self.process.pid if self.process is not None else None,
            poll_interval=self.poll_interval,
            max_jobs=self.max_jobs,
            last_exit_code=self.last_exit_code,
        )

    def start(self, *, poll_interval: float = 2.0, max_jobs: int | None = None) -> WorkerStatusResponse:
        current = self.status()
        if current.state == "running":
            return current

        env = os.environ.copy()
        src_path = str(self.project_root / "src")
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = f"{src_path}:{existing_pythonpath}" if existing_pythonpath else src_path

        command = [
            self.python_executable,
            "-m",
            "gemma_tutor_edge.worker",
            "--poll-interval",
            str(poll_interval),
        ]
        if max_jobs is not None:
            command.extend(["--max-jobs", str(max_jobs)])

        self.process = subprocess.Popen(
            command,
            cwd=self.project_root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self.poll_interval = poll_interval
        self.max_jobs = max_jobs
        self.last_exit_code = None
        return self.status()

    def stop(self) -> WorkerStatusResponse:
        current = self.status()
        if current.state == "stopped" or self.process is None:
            return current

        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)

        self.last_exit_code = self.process.returncode
        self.process = None
        self.poll_interval = None
        self.max_jobs = None
        return self.status()
