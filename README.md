# Knowledge Wiki

Local-first personal knowledge wiki. Obsidian is the reading UI, Telegram is the
capture/chat interface, Ollama provides local models, and an LLM maintains the
Markdown wiki under `wiki/`. See `plan.md` for the design and `AGENTS.md` for the
rules the LLM follows.

## Layers
- `raw/` immutable original sources
- `processed/` reproducible extraction output (transcripts, OCR, metadata)
- `wiki/` LLM-maintained pages, plus `index.md` and append-only `log.md`
- `data/state.db` SQLite job and dedupe state

## Setup (Windows)
1. `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
2. `pip install -r requirements-dev.txt`
3. Install FFmpeg, yt-dlp, ExifTool (winget) and Ollama; `ollama pull qwen3:8b qwen3-vl:8b embeddinggemma`
4. Copy `.env.example` to `.env` and fill in the Telegram token and your user ID
5. Run: `python -m scripts.app`

## Security
- Only users in `TELEGRAM_ALLOWED_USER_IDS` are served.
- `config/privacy.yaml` is enforced before every LLM request; private sources never go to cloud.
- Never commit `.env`. Do not send highly sensitive files through Telegram.
