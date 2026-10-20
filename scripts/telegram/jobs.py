"""Job execution and reporting for Telegram captures. No source content is logged or echoed."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select

from scripts.config import Vault
from scripts.database import Job, Source, open_db
from scripts.extractors.tools import ExtractionError
from scripts.providers.base import CloudBlocked, ProviderUnavailable
from scripts.security import PathRejected, UrlRejected, redact_secrets
from scripts.wiki.ingest import IngestError, IngestResult

log = logging.getLogger("knowledge_wiki.telegram")

Send = Callable[[str], Awaitable[Any]]
Work = Callable[[Callable[[int], None]], IngestResult]
MAX_LISTED = 10
ACTIVE = ("queued", "running")


def default_privacy(vault: Vault, source_type: str | None) -> str:
    if not source_type:
        return "per config/privacy.yaml"
    cfg = vault.privacy
    return str(cfg.get("source_defaults", {}).get(source_type, cfg.get("default_classification")))


def _lines(title: str, items: list[str]) -> str:
    shown = [f"- {i}" for i in items[:MAX_LISTED]]
    if len(items) > MAX_LISTED:
        shown.append(f"- ... and {len(items) - MAX_LISTED} more")
    return f"{title}\n" + "\n".join(shown)


def format_result(result: IngestResult) -> str:
    if result.status == "duplicate":
        return f"Already ingested.\n\nSource summary:\n{result.summary_path}"
    parts = [
        f"Processing complete.\nJob ID: {result.job_id}",
        f"Source summary:\n{result.summary_path}",
    ]
    if result.book_path:
        parts.append(f"Book page:\n{result.book_path}")
    changed = [f"wiki/topics/{s}.md" for s in [*result.created, *result.updated]]
    if changed:
        parts.append(_lines("Updated pages:", changed))
    if result.needs_review:
        parts.append(_lines("Needs review:", result.needs_review))
    return "\n\n".join(parts)


class JobRunner:
    """Runs blocking ingest work off the event loop, one at a time (the GPU is shared)."""

    def __init__(self, vault: Vault):
        self.vault = vault
        self.tasks: dict[int, asyncio.Task[Any]] = {}
        self.gate = asyncio.Semaphore(1)

    async def run(
        self,
        send: Send,
        label: str,
        kind: str,
        source_type: str | None,
        provider: str,
        work: Work,
        extra: Callable[[IngestResult], str] | None = None,
    ) -> IngestResult | None:
        await send(
            f"Received: {label}\nType: {kind}\n"
            f"Privacy: {default_privacy(self.vault, source_type)}\n"
            f"Provider: {provider}\nStatus: queued"
        )
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        started: list[int] = []

        def on_job(job_id: int) -> None:
            started.append(job_id)
            if task:
                self.tasks[job_id] = task
            note = f"Job ID: {job_id}  (/status {job_id}, /cancel {job_id})"
            asyncio.run_coroutine_threadsafe(send(note), loop)

        try:
            async with self.gate:
                result = await asyncio.to_thread(work, on_job)
        except asyncio.CancelledError:
            await send("Cancelled. A step that was already running may still finish.")
            return None
        except (PathRejected, UrlRejected) as exc:
            await send(f"Rejected: {redact_secrets(str(exc))}")
        except CloudBlocked as exc:
            await send(f"Blocked: {redact_secrets(str(exc))}")
        except (ProviderUnavailable, IngestError, ExtractionError, OSError) as exc:
            retry = f"\nRetry with /retry {started[-1]}" if started else ""
            await send(f"Failed: {redact_secrets(str(exc))}{retry}")
        except Exception as exc:
            log.error("unexpected failure: %s", type(exc).__name__)
            await send(f"Failed: unexpected error ({type(exc).__name__}).")
        else:
            text = format_result(result)
            if extra and result.status != "duplicate":
                text += "\n\n" + extra(result)
            await send(text)
            return result
        finally:
            for job_id in started:
                self.tasks.pop(job_id, None)
        return None


def describe_job(vault: Vault, job_id: int) -> str:
    db = open_db(vault.path("database"))
    try:
        job = db.get(Job, job_id)
        source = db.get(Source, job.source_id) if job else None
        if not job or not source:
            return f"No job {job_id}."
        lines = [
            f"Job {job.id}: {job.status}",
            f"Source: {source.original_name} ({source.source_type}, {source.privacy})",
            f"Retries: {job.retry_count}",
        ]
        if job.error_message:
            lines.append(f"Error: {redact_secrets(job.error_message)[:300]}")
        if source.summary_path:
            lines.append(f"Source summary: {source.summary_path}")
        return "\n".join(lines)
    finally:
        db.close()


def recent_jobs(vault: Vault, limit: int = 5) -> str:
    db = open_db(vault.path("database"))
    try:
        jobs = db.scalars(select(Job).order_by(Job.id.desc()).limit(limit)).all()
        if not jobs:
            return "No jobs yet."
        rows = []
        for job in jobs:
            source = db.get(Source, job.source_id)
            rows.append(f"{job.id}: {job.status} - {source.original_name if source else '?'}")
        return "Recent jobs:\n" + "\n".join(rows)
    finally:
        db.close()


def cancel_job(runner: JobRunner, job_id: int) -> str:
    db = open_db(runner.vault.path("database"))
    try:
        job = db.get(Job, job_id)
        if not job:
            return f"No job {job_id}."
        if job.status == "done":
            return f"Job {job_id} is already complete; nothing to cancel."
        if job.status == "cancelled":
            return f"Job {job_id} is already cancelled."
        job.status = "cancelled"
        db.commit()
    finally:
        db.close()
    task = runner.tasks.get(job_id)
    if task:
        task.cancel()
    return f"Job {job_id} cancelled. Pages already written are kept."


def retry_target(vault: Vault, job_id: int) -> tuple[str, int] | str:
    """(raw path, retry number) for a failed job, or a refusal message. Retries are bounded."""
    limit = int(vault.settings.get("limits", {}).get("max_retries", 3))
    db = open_db(vault.path("database"))
    try:
        job = db.get(Job, job_id)
        source = db.get(Source, job.source_id) if job else None
        if not job or not source:
            return f"No job {job_id}."
        if source.status == "done":
            return f"Job {job_id}: this source was already ingested ({source.summary_path})."
        if job.status != "failed":
            return f"Job {job_id} is {job.status}; only failed jobs can be retried."
        if job.retry_count >= limit:
            return f"Job {job_id} has been retried {limit} times; check the error with /status."
        job.retry_count += 1
        db.commit()
        return source.raw_path, job.retry_count
    finally:
        db.close()
