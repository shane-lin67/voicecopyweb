from __future__ import annotations

import json
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Job:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = "queued"
    stage: str = "等待处理"
    progress: int = 0
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    events: queue.Queue[dict[str, Any]] = field(default_factory=queue.Queue)

    def update(self, stage: str, progress: int, **extra: Any) -> None:
        self.status = "running"
        self.stage = stage
        self.progress = progress
        self.events.put({"type": "progress", "stage": stage, "progress": progress, **extra})

    def complete(self, result: str) -> None:
        self.status = "completed"
        self.stage = "完成"
        self.progress = 100
        self.result = result
        self.events.put({"type": "complete", "progress": 100, "result": result})

    def fail(self, message: str) -> None:
        self.status = "failed"
        self.error = message
        self.events.put({"type": "error", "message": message})


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job = Job()
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)


jobs = JobStore()


def event_json(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

