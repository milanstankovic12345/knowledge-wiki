"""Bot assembly and long polling. The bot only starts with a token and a non-empty allowlist."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from scripts.config import Vault
from scripts.telegram import handlers as h
from scripts.telegram.jobs import JobRunner

log = logging.getLogger("knowledge_wiki.telegram")


class BotConfigError(RuntimeError):
    pass


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Only the exception type is logged: messages can carry source content or the bot token.
    log.error("update failed: %s", type(context.error).__name__)


def build_application(vault: Vault) -> Application:
    token = vault.provider.telegram_bot_token.get_secret_value()
    allowed = vault.provider.allowed_user_ids
    if not token:
        raise BotConfigError("TELEGRAM_BOT_TOKEN is not set in .env")
    if not allowed:
        raise BotConfigError("TELEGRAM_ALLOWED_USER_IDS is empty; refusing to start an open bot")

    app = (
        ApplicationBuilder()
        .token(token)
        .concurrent_updates(True)
        .connect_timeout(20)
        .read_timeout(30)
        .write_timeout(60)  # photo/document downloads and uploads
        .pool_timeout(20)
        .get_updates_connect_timeout(20)
        .get_updates_read_timeout(40)
        .build()
    )
    app.bot_data["state"] = h.AppState(vault, allowed, JobRunner(vault))

    commands = {
        "start": h.cmd_start,
        "help": h.cmd_start,
        "status": h.cmd_status,
        "provider": h.cmd_provider,
        "privacy": h.cmd_privacy,
        "ingest": h.cmd_ingest,
        "ingest_local": h.cmd_ingest_local,
        "retry": h.cmd_retry,
        "cancel": h.cmd_cancel,
        "search": h.cmd_search,
        "ask": h.cmd_ask,
        "compare": h.cmd_compare,
        "summarize": h.cmd_summarize,
        "link": h.cmd_link,
        "lint": h.cmd_lint,
    }
    for name, callback in commands.items():
        app.add_handler(CommandHandler(name, callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, h.on_text))
    app.add_handler(CallbackQueryHandler(h.on_choice, pattern=r"^pick:"))
    app.add_handler(CallbackQueryHandler(h.on_link_choice, pattern=r"^link:"))
    app.add_handler(MessageHandler(filters.PHOTO, h.on_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, h.on_document))
    app.add_handler(MessageHandler(filters.VOICE, h.on_voice))
    app.add_handler(MessageHandler(filters.AUDIO, h.on_audio))
    app.add_handler(MessageHandler(filters.VIDEO, h.on_video))
    app.add_error_handler(on_error)
    return app


def run_bot(vault: Vault) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    # httpx logs full request URLs at INFO, and Telegram API URLs contain the bot token.
    for noisy in ("httpx", "httpcore", "telegram", "apscheduler"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    app = build_application(vault)
    log.info("bot started (long polling, %d allowed user(s))", len(vault.provider.allowed_user_ids))
    # Retry the startup handshake instead of aborting on one slow response (-1 = keep trying).
    app.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=-1)
