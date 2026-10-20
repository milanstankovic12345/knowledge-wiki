"""Telegram update handlers. Telegram is a transport: every capture goes through the ingest
pipeline, and no handler runs shell commands or accepts a path outside `raw/`."""

from __future__ import annotations

import asyncio
import functools
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from scripts.config import Vault
from scripts.extractors.url import capture_article
from scripts.providers.base import CloudBlocked, ProviderUnavailable
from scripts.providers.embeddings import OllamaEmbedder
from scripts.providers.router import select_provider, select_vision_provider
from scripts.security import redact_secrets
from scripts.storage import dump_frontmatter, parse_frontmatter, slugify
from scripts.telegram import intent, query
from scripts.telegram.jobs import (
    JobRunner,
    cancel_job,
    describe_job,
    recent_jobs,
    retry_target,
)
from scripts.wiki import link
from scripts.wiki.ingest import IngestResult, ingest_carousel, ingest_file
from scripts.wiki.lint import format_report, run_lint

log = logging.getLogger("knowledge_wiki.telegram")

URL_ONLY = re.compile(r"https?://\S+")
URL_IN_TEXT = re.compile(r"https?://[^\s<>\"')]+")
PROVIDERS = ("local", "ollama-cloud", "openai-compatible", "hybrid")
PRIVACY_CLASSES = ("public", "personal", "confidential", "restricted")
TRANSCRIPT_PREVIEW_CHARS = 300
MARKERS = re.compile(r"<!--.*?-->")

HELP = """Just type, no commands needed:
- ask a question and I answer from the wiki
- write a thought or start with "save:" and I keep it as a note
- if I can't tell, I ask you with two buttons

Send me something to capture it:
- an article URL (also inside a sentence)
- a PDF or other document, a voice note, audio, video
- a photo, or several photos as one album
- /ingest <text or URL> to save a note

Commands:
/status [id] - recent jobs or one job
/retry <id> - retry a failed job
/cancel <id> - cancel a job
/provider [local|ollama-cloud|hybrid]
/privacy [public|personal|confidential|restricted]
/ingest_local <path under raw/> - for large files copied into raw/ yourself
/search <words> - search the wiki
/ask <question> - answer from the wiki, with sources
/compare <question> - compare positions in the wiki
/summarize <title> - stored summary of a source
/lint - check the wiki for broken links, orphans and missing sources
/link - suggest missing links between related pages; you approve each one

Never send passwords, keys or identity documents. Telegram itself can read what you send."""


@dataclass
class Group:
    message: Any  # first message of the album, used for replies
    chat_id: int
    items: dict[int, Any] = field(default_factory=dict)  # message_id -> PhotoSize
    captions: dict[int, str] = field(default_factory=dict)
    task: asyncio.Task[Any] | None = None


@dataclass
class AppState:
    vault: Vault
    allowed: frozenset[int]
    runner: JobRunner
    groups: dict[str, Group] = field(default_factory=dict)
    # Swappable seams (tests inject fakes here).
    ingest: Callable[..., IngestResult] = ingest_file
    ingest_group: Callable[..., IngestResult] = ingest_carousel
    capture: Callable[..., Path] = capture_article
    select_text: Callable[..., Any] = select_provider
    select_vision: Callable[..., Any] = select_vision_provider
    classify: Callable[..., intent.Decision] = intent.classify
    embedder: Callable[[Vault], Any] = lambda v: OllamaEmbedder(  # noqa: E731
        v.provider.ollama_local_url,
        v.provider.ollama_local_embed_model,
        keep_alive=str(v.settings.get("models", {}).get("keep_alive", "30s")),
    )


Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE, AppState], Awaitable[None]]


def authorized(fn: Handler) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]:
    """Silently drop every update that is not from an allowlisted user in a private chat."""

    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        state: AppState = context.application.bot_data["state"]
        user, chat = update.effective_user, update.effective_chat
        if user is None or user.id not in state.allowed or chat is None or chat.type != "private":
            log.warning("rejected update from user id %s", user.id if user else None)
            return
        await fn(update, context, state)

    return wrapper


def clip(vault: Vault, text: str) -> str:
    limit = int(vault.settings.get("telegram", {}).get("reply_max_chars", 3500))
    text = redact_secrets(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def sender(update: Update, state: AppState) -> Callable[[str], Awaitable[Any]]:
    message = update.effective_message

    async def send(text: str) -> Any:
        return await message.reply_text(clip(state.vault, text))

    return send


def chat_provider(context: ContextTypes.DEFAULT_TYPE, state: AppState) -> str:
    return context.chat_data.get("provider") or state.vault.provider.llm_provider


def factories(context: ContextTypes.DEFAULT_TYPE, state: AppState) -> dict[str, Any]:
    requested = context.chat_data.get("provider")
    return {
        "provider_factory": lambda v, p, s, r: state.select_text(v, p, s, r, requested),
        "vision_factory": lambda v, p, s, r: state.select_vision(v, p, s, r, requested),
    }


# --- saving captures under raw/telegram ---------------------------------------------------------


def telegram_dir(vault: Vault) -> Path:
    folder = vault.path("raw") / "telegram"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def new_raw_path(vault: Vault, stem: str, ext: str) -> Path:
    """A fresh, never-overwritten file name. Raw captures are immutable."""
    base = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(stem, 40)}"
    folder = telegram_dir(vault)
    path, n = folder / f"{base}{ext}", 1
    while path.exists():
        n += 1
        path = folder / f"{base}-{n}{ext}"
    return path


def allowed_extensions(vault: Vault) -> set[str]:
    exts = vault.settings["allowed_extensions"]
    return {e for kind in ("document", "audio", "video", "image") for e in exts[kind]}


def save_note(vault: Vault, text: str, author: str = "", privacy: str = "") -> Path:
    meta: dict[str, Any] = {
        "title": (text.strip().splitlines() or ["Note"])[0][:60],
        "source_type": "telegram_text",
        "author": author,
        "captured_at": datetime.now().date().isoformat(),
    }
    if privacy:
        meta["privacy"] = privacy
    path = new_raw_path(vault, "note", ".md")
    path.write_text(dump_frontmatter(meta, text.strip() + "\n"), encoding="utf-8")
    return path


def forward_author(message: Any) -> str:
    origin = getattr(message, "forward_origin", None)
    if origin is None:
        return ""
    for attr in ("sender_user", "chat", "sender_chat"):
        who = getattr(origin, attr, None)
        name = getattr(who, "full_name", None) or getattr(who, "title", None)
        if name:
            return str(name)
    return str(getattr(origin, "sender_user_name", "") or "")


def too_large(vault: Vault, size: int | None) -> bool:
    limit = int(vault.settings.get("telegram", {}).get("max_file_mb", 20)) * 1024 * 1024
    return bool(size and size > limit)


LARGE_FILE = (
    "That file is over Telegram's bot download limit. Copy it into the right raw/ folder on "
    "the computer yourself, then send /ingest_local raw/<folder>/<file>."
)


# --- plain captures -----------------------------------------------------------------------------


async def capture_url(update: Update, context, state: AppState, url: str) -> None:
    privacy = context.chat_data.get("privacy", "")
    kw = factories(context, state)

    def work(on_job):
        path = state.capture(url, state.vault, privacy=privacy)
        return state.ingest(state.vault, path, on_job=on_job, **kw)

    await state.runner.run(
        sender(update, state), url, "article", "article", chat_provider(context, state), work
    )


async def capture_note(update: Update, context, state: AppState, text: str) -> None:
    author = forward_author(update.effective_message)
    path = save_note(state.vault, text, author, context.chat_data.get("privacy", ""))
    kw = factories(context, state)
    await state.runner.run(
        sender(update, state),
        path.name,
        "note",
        "telegram_text",
        chat_provider(context, state),
        lambda on_job: state.ingest(state.vault, path, on_job=on_job, **kw),
    )


@authorized
async def on_text(update: Update, context, state: AppState) -> None:
    message = update.effective_message
    text = (message.text or "").strip()
    if not text:
        return
    if URL_ONLY.fullmatch(text):
        await capture_url(update, context, state, text)
    elif getattr(message, "forward_origin", None):
        await capture_note(update, context, state, text)
    elif found := URL_IN_TEXT.search(text):
        await capture_url(update, context, state, found.group(0))
    elif intent.is_greeting(text):
        await sender(update, state)(HELP)
    else:
        decision = await asyncio.to_thread(state.classify, state.vault, text, state.select_text)
        if decision.label == "question":
            await answer_question(update, context, state, decision.text, compare=False)
        elif decision.label == "note":
            await capture_note(update, context, state, decision.text)
        else:
            await offer_choice(update, context, state, text)


PENDING_LIMIT = 20
LINK_SUGGESTIONS = 5


async def offer_choice(update: Update, context, state: AppState, text: str) -> None:
    """Ask once instead of guessing. The text stays server-side; buttons carry only an id."""
    message = update.effective_message
    pending = context.chat_data.setdefault("pending", {})
    pending[message.message_id] = text
    while len(pending) > PENDING_LIMIT:
        pending.pop(next(iter(pending)))
    mid = message.message_id
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("Answer it", callback_data=f"pick:ask:{mid}"),
            InlineKeyboardButton("Save as note", callback_data=f"pick:note:{mid}"),
        ]]
    )  # fmt: skip
    await message.reply_text("Do you want an answer from the wiki, or should I save this?",
                             reply_markup=keyboard)  # fmt: skip


@authorized
async def on_choice(update: Update, context, state: AppState) -> None:
    query_ = update.callback_query
    await query_.answer()
    match = re.fullmatch(r"pick:(ask|note):(\d+)", query_.data or "")
    if not match:
        return
    text = context.chat_data.get("pending", {}).pop(int(match.group(2)), None)
    if text is None:
        await sender(update, state)("That choice expired. Send the message again.")
        return
    await query_.edit_message_reply_markup(reply_markup=None)
    if match.group(1) == "ask":
        await answer_question(update, context, state, text, compare=False)
    else:
        await capture_note(update, context, state, text)


@authorized
async def cmd_ingest(update: Update, context, state: AppState) -> None:
    text = " ".join(context.args or []).strip()
    if not text:
        await sender(update, state)("Usage: /ingest <text or URL>")
    elif URL_ONLY.fullmatch(text):
        await capture_url(update, context, state, text)
    else:
        await capture_note(update, context, state, text)


async def save_and_ingest(
    update: Update,
    context,
    state: AppState,
    media: Any,
    ext: str,
    stem: str,
    kind: str,
    source_type: str,
    caption: str = "",
    extra: Callable[[IngestResult], str] | None = None,
) -> None:
    send = sender(update, state)
    if too_large(state.vault, getattr(media, "file_size", None)):
        await send(LARGE_FILE)
        return
    if ext.lower() not in allowed_extensions(state.vault):
        await send(f"Unsupported file type {ext or '(none)'}.")
        return
    path = new_raw_path(state.vault, stem, ext.lower())
    await (await media.get_file()).download_to_drive(custom_path=path)
    if caption.strip():
        path.with_suffix(".caption.txt").write_text(caption.strip() + "\n", encoding="utf-8")
    kw = factories(context, state)
    await state.runner.run(
        send,
        path.name,
        kind,
        source_type,
        chat_provider(context, state),
        lambda on_job: state.ingest(state.vault, path, on_job=on_job, **kw),
        extra,
    )


def transcript_preview(vault: Vault) -> Callable[[IngestResult], str]:
    """A short preview of the stored transcript, never the whole private recording."""

    def preview(result: IngestResult) -> str:
        meta, _ = parse_frontmatter((vault.root / result.summary_path).read_text("utf-8"))
        processed = [p for p in meta.get("processed_paths", []) if str(p).endswith(".md")]
        if not processed:
            return ""
        text = (vault.root / processed[0]).read_text("utf-8")
        _, body = parse_frontmatter(text)
        flat = " ".join(MARKERS.sub(" ", body).split())
        return f"Transcript preview:\n{flat[:TRANSCRIPT_PREVIEW_CHARS]}"

    return preview


@authorized
async def on_document(update: Update, context, state: AppState) -> None:
    message = update.effective_message
    doc = message.document
    name = doc.file_name or "document"
    ext = Path(name).suffix
    await save_and_ingest(
        update, context, state, doc, ext, Path(name).stem, "document", "telegram_document",
        message.caption or "",
    )  # fmt: skip


@authorized
async def on_voice(update: Update, context, state: AppState) -> None:
    await save_and_ingest(
        update, context, state, update.effective_message.voice, ".ogg", "voice", "voice",
        "telegram_voice", extra=transcript_preview(state.vault),
    )  # fmt: skip


@authorized
async def on_audio(update: Update, context, state: AppState) -> None:
    audio = update.effective_message.audio
    name = audio.file_name or "audio.mp3"
    await save_and_ingest(
        update, context, state, audio, Path(name).suffix or ".mp3", Path(name).stem, "audio",
        "telegram_voice", extra=transcript_preview(state.vault),
    )  # fmt: skip


@authorized
async def on_video(update: Update, context, state: AppState) -> None:
    video = update.effective_message.video
    name = video.file_name or "video.mp4"
    await save_and_ingest(
        update, context, state, video, Path(name).suffix or ".mp4", Path(name).stem, "video",
        "pc_video",
    )  # fmt: skip


# --- photos and albums --------------------------------------------------------------------------


@authorized
async def on_photo(update: Update, context, state: AppState) -> None:
    message = update.effective_message
    photo = message.photo[-1]  # largest size
    gid = message.media_group_id
    if not gid:
        await save_and_ingest(
            update, context, state, photo, ".jpg", "photo", "photo", "telegram_photo",
            message.caption or "",
        )  # fmt: skip
        return
    group = state.groups.get(gid)
    if group is None:
        group = state.groups[gid] = Group(message, update.effective_chat.id)
    group.items[message.message_id] = photo
    if message.caption:
        group.captions[message.message_id] = message.caption
    if group.task:
        group.task.cancel()  # a new album message restarts the wait
    group.task = asyncio.create_task(flush_group(update, context, state, str(gid)))


async def flush_group(update: Update, context, state: AppState, gid: str) -> None:
    wait = float(state.vault.settings.get("telegram", {}).get("media_group_wait_seconds", 2))
    await asyncio.sleep(wait)
    group = state.groups.pop(gid, None)  # from here on a late message starts a new album
    if group is None:
        return
    send = sender(update, state)
    if any(too_large(state.vault, getattr(p, "file_size", None)) for p in group.items.values()):
        await send(LARGE_FILE)
        return
    folder = telegram_dir(state.vault) / f"media-group-{slugify(gid, 40)}"
    folder.mkdir(exist_ok=True)
    for n, message_id in enumerate(sorted(group.items), start=1):  # message order = album order
        dest = folder / f"{n:03d}.jpg"
        if not dest.exists():
            await (await group.items[message_id].get_file()).download_to_drive(custom_path=dest)
    caption = next((group.captions[m] for m in sorted(group.captions)), "")
    if caption.strip() and not (folder / "caption.txt").exists():
        (folder / "caption.txt").write_text(caption.strip() + "\n", encoding="utf-8")
        found = URL_IN_TEXT.search(caption)
        if found:
            (folder / "original-url.txt").write_text(found.group(0) + "\n", encoding="utf-8")
    kw = factories(context, state)
    await state.runner.run(
        send,
        folder.name,
        f"photo album ({len(group.items)} images)",
        "telegram_photo",
        chat_provider(context, state),
        lambda on_job: state.ingest_group(state.vault, folder, on_job=on_job, **kw),
    )


# --- commands -----------------------------------------------------------------------------------


@authorized
async def cmd_start(update: Update, context, state: AppState) -> None:
    await sender(update, state)(HELP)


@authorized
async def cmd_status(update: Update, context, state: AppState) -> None:
    arg = (context.args or [""])[0]
    if arg.isdigit():
        text = describe_job(state.vault, int(arg))
    else:
        text = recent_jobs(state.vault)
        text += f"\nProvider: {chat_provider(context, state)}"
        text += f"\nPrivacy default: {context.chat_data.get('privacy', 'per source type')}"
    await sender(update, state)(text)


@authorized
async def cmd_provider(update: Update, context, state: AppState) -> None:
    send = sender(update, state)
    value = (context.args or [""])[0].lower()
    if not value:
        await send(f"Provider: {chat_provider(context, state)}. Options: {', '.join(PROVIDERS)}")
    elif value not in PROVIDERS:
        await send(f"Unknown provider. Options: {', '.join(PROVIDERS)}")
    else:
        context.chat_data["provider"] = value
        note = "" if value == "local" else (
            "\nCloud providers are not available yet, and private sources are never sent to "
            "the cloud; requests will fail safely rather than fall back."
        )  # fmt: skip
        await send(f"Provider set to {value} for this chat.{note}")


@authorized
async def cmd_privacy(update: Update, context, state: AppState) -> None:
    send = sender(update, state)
    value = (context.args or [""])[0].lower()
    if not value:
        classes = state.vault.privacy.get("classifications", {})
        lines = [f"{c}: cloud {'allowed' if v.get('allow_cloud') else 'blocked'}"
                 for c, v in classes.items()]  # fmt: skip
        current = context.chat_data.get("privacy", "per source type")
        await send(f"Privacy default for notes and URLs: {current}\n" + "\n".join(lines))
    elif value not in PRIVACY_CLASSES:
        await send(f"Unknown class. Options: {', '.join(PRIVACY_CLASSES)}")
    else:
        context.chat_data["privacy"] = value
        await send(
            f"New notes and URLs from this chat are classified {value}. "
            "Files, photos and recordings keep their type defaults."
        )


@authorized
async def cmd_ingest_local(update: Update, context, state: AppState) -> None:
    send = sender(update, state)
    arg = " ".join(context.args or []).strip()
    if not arg:
        await send("Usage: /ingest_local raw/<folder>/<file>")
        return
    vault = state.vault
    candidate = (vault.root / arg).resolve()
    kw = factories(context, state)
    if candidate.is_dir():
        run = lambda on_job: state.ingest_group(vault, arg, on_job=on_job, **kw)  # noqa: E731
    else:
        run = lambda on_job: state.ingest(vault, arg, on_job=on_job, **kw)  # noqa: E731
    await state.runner.run(send, arg, "local file", None, chat_provider(context, state), run)


@authorized
async def cmd_retry(update: Update, context, state: AppState) -> None:
    send = sender(update, state)
    arg = (context.args or [""])[0]
    if not arg.isdigit():
        await send("Usage: /retry <job id>")
        return
    target = retry_target(state.vault, int(arg))
    if isinstance(target, str):
        await send(target)
        return
    raw_path, _ = target
    kw = factories(context, state)
    is_dir = (state.vault.root / raw_path).is_dir()
    run = state.ingest_group if is_dir else state.ingest
    await state.runner.run(
        send, raw_path, "retry", None, chat_provider(context, state),
        lambda on_job: run(state.vault, raw_path, on_job=on_job, **kw),
    )  # fmt: skip


@authorized
async def cmd_cancel(update: Update, context, state: AppState) -> None:
    arg = (context.args or [""])[0]
    text = cancel_job(state.runner, int(arg)) if arg.isdigit() else "Usage: /cancel <job id>"
    await sender(update, state)(text)


@authorized
async def cmd_search(update: Update, context, state: AppState) -> None:
    send = sender(update, state)
    text = " ".join(context.args or []).strip()
    if not text:
        await send("Usage: /search <words>")
        return
    limit = int(state.vault.settings.get("telegram", {}).get("search_results", 5))
    hits = await asyncio.to_thread(
        query.search_wiki, state.vault, text, limit, state.embedder(state.vault)
    )
    if not hits:
        await send("No wiki pages match.")
        return
    await send("\n\n".join(f"{n}. {h.path}\n{h.snippet}" for n, h in enumerate(hits, start=1)))


async def _answer(update: Update, context, state: AppState, compare: bool) -> None:
    question = " ".join(context.args or []).strip()
    if not question:
        await sender(update, state)(
            "Usage: /ask <question>" if not compare else "Usage: /compare <question>"
        )
        return
    await answer_question(update, context, state, question, compare)


async def answer_question(
    update: Update, context, state: AppState, question: str, compare: bool
) -> None:
    send = sender(update, state)
    try:
        text = await asyncio.to_thread(
            query.ask_wiki,
            state.vault,
            question,
            context.chat_data.get("provider"),
            compare,
            state.select_text,
            state.embedder(state.vault),
        )
    except CloudBlocked as exc:
        text = f"Blocked: {exc}"
    except ProviderUnavailable as exc:
        text = f"Failed: {exc}"
    await send(text)


@authorized
async def cmd_ask(update: Update, context, state: AppState) -> None:
    await _answer(update, context, state, compare=False)


@authorized
async def cmd_compare(update: Update, context, state: AppState) -> None:
    await _answer(update, context, state, compare=True)


@authorized
async def cmd_summarize(update: Update, context, state: AppState) -> None:
    text = " ".join(context.args or []).strip()
    reply = query.summary_of(state.vault, text) if text else "Usage: /summarize <title words>"
    await sender(update, state)(reply)


@authorized
async def cmd_lint(update: Update, context, state: AppState) -> None:
    report = await asyncio.to_thread(run_lint, state.vault)
    await sender(update, state)(format_report(report))


@authorized
async def cmd_link(update: Update, context, state: AppState) -> None:
    send = sender(update, state)
    embedder = state.embedder(state.vault)
    try:
        if embedder is None:
            raise ProviderUnavailable("no embedder")
        found = await asyncio.to_thread(link.suggest_links, state.vault, embedder, LINK_SUGGESTIONS)
    except ProviderUnavailable:
        await send("Link suggestions need the local embedding model (ollama).")
        return
    if not found:
        await send("No missing links found between topic and concept pages.")
        return
    # Pairs stay server-side; buttons carry only an id (same pattern as offer_choice).
    pending = context.chat_data.setdefault("link_pending", {})
    message = update.effective_message
    lines, buttons = [], []
    for n, s in enumerate(found, start=1):
        key = f"{message.message_id}-{n}"
        pending[key] = (s.a, s.b)
        lines.append(f"{n}. {s.a} <-> {s.b} ({s.similarity:.2f})")
        buttons.append(InlineKeyboardButton(f"Link {n}", callback_data=f"link:{key}"))
    while len(pending) > PENDING_LIMIT:
        pending.pop(next(iter(pending)))
    await message.reply_text(
        clip(state.vault, "Suggested links (nothing changes until you press a button):\n"
             + "\n".join(lines)),
        reply_markup=InlineKeyboardMarkup([buttons[i : i + 3] for i in range(0, len(buttons), 3)]),
    )  # fmt: skip


@authorized
async def on_link_choice(update: Update, context, state: AppState) -> None:
    query_ = update.callback_query
    await query_.answer()
    match = re.fullmatch(r"link:(\d+-\d+)", query_.data or "")
    if not match:
        return
    pair = context.chat_data.get("link_pending", {}).pop(match.group(1), None)
    if pair is None:
        await sender(update, state)("That link suggestion expired. Run /link again.")
        return
    try:
        changed = await asyncio.to_thread(link.apply_link, state.vault, *pair)
    except ValueError:
        await sender(update, state)("One of those pages no longer exists. Run /link again.")
        return
    done = "Linked" if changed else "Already linked"
    await sender(update, state)(f"{done}: {pair[0]} <-> {pair[1]}")


@authorized
async def cmd_unavailable(update: Update, context, state: AppState) -> None:
    await sender(update, state)("That command is not available yet.")
