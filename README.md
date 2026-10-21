# Knowledge Wiki

A **local-first, LLM-maintained personal knowledge base**. You drop in articles, PDFs, books,
videos, voice notes and photos (from your phone via Telegram, or from your PC). A local language
model reads each one, writes a source-linked summary, and weaves the ideas into a growing web of
interlinked Markdown pages that you browse in Obsidian and query by chatting with a bot.

It is built around one idea: **the model does the bookkeeping, you do the thinking, and your
private data never leaves your machine unless a written policy allows it.**

---

## 1. What this project demonstrates

| Topic | How it is applied here |
|---|---|
| **LLM-maintained knowledge (a "compounding wiki")** | Instead of re-reading sources, the LLM incrementally maintains durable topic pages. Each new source updates existing pages, adds backlinks and records contradictions rather than overwriting them. |
| **Retrieval and RAG** | `/ask` searches the wiki, passes the best pages to the model, and returns *Answer, Sources, Uncertainty, Related pages*. The wiki itself is a curated retrieval layer. See `wiki/topics/retrieval-augmented-generation-rag.md` and `agentic-rag.md`, which the system built from sources I fed it. |
| **Local models and cost control** | Text uses `qwen3:8b`, vision uses `qwen3-vl:8b`, speech-to-text uses faster-whisper, all on a single 8 GB GPU through Ollama. Cost: electricity only. Models unload quickly (`keep_alive: 30s`) and jobs run one at a time to fit VRAM. |
| **Privacy by design / data governance** | Every source gets a privacy class. `config/privacy.yaml` is enforced in code (`scripts/providers/router.py`) before any model call. Local-only paths (`raw/telegram`, `raw/books`, `raw/photos`, `raw/videos`) can never reach a cloud provider, and the model cannot decide otherwise. |
| **Prompt-injection defence** | All source text and chat messages are wrapped as *untrusted data* (`scripts/security.py`). Instructions hidden in an article, transcript, caption or Telegram message are never followed, and the bot cannot run shell commands. This is covered by tests. |
| **Grounding and hallucination control** | Every factual claim must link to a source-summary page. Answers state their uncertainty and quote the pages they rely on; each quote is string-checked against the text the model was given, and unfound quotes trigger a warning. Contradictions are kept under a History/Contradictions section. Model output is schema-validated JSON with retries. |
| **Multimodal pipeline** | PDF/EPUB/DOCX (Docling), audio and video transcription (faster-whisper), video frames and photos described by a vision model, web articles (trafilatura), YouTube subtitles (yt-dlp). |
| **Agentic UX** | A local model classifies plain Telegram messages as *question* or *note* and routes them; when unsure it asks with two buttons. No commands needed. |
| **Engineering quality** | Provider abstraction (local Ollama, Ollama Cloud, OpenAI-compatible), SHA-256 de-duplication, SQLite job state with retry/cancel, ~150 automated tests, Ruff lint, Git history for rollback. |

**Retrieval quality.** `/ask` and `/search` blend keyword scores with embedding similarity
(`config/settings.yaml` -> `search`). For example, "how do I make retrieval cheaper?" now surfaces
`cost-optimization` even though that page shares almost no words with the question.

**Live example.** The wiki already contains pages the system generated from real sources I fed it:
an article on RAG systems, one on agentic RAG, one on cutting file-search cost with Claude Code,
a book on Android programming, and a Python tutorial video. Open `index.md` or the Obsidian graph
view to see how ideas from different sources link together.

---

## 2. How it works

```
 Telegram / Obsidian Web Clipper / files copied to raw/
                    |
                    v
   Ingest: detect type -> SHA-256 de-dupe -> privacy class
                    |
                    v
   raw/        original, immutable
                    |
                    v
   processed/  transcripts, OCR, extracted Markdown (reproducible)
                    |
                    v
   Local LLM: summary, main ideas, claims, concepts, open questions
                    |
                    v
   wiki/       source summaries + topic pages + index.md + log.md
                    |
                    v
   Obsidian (read, graph, edit)      Telegram (ask, search, compare)
```

| Folder | Role | Who writes it |
|---|---|---|
| `raw/` | Original sources. **Never modified.** | You / the bot (new files only) |
| `processed/` | Transcripts, OCR text, image descriptions. Can be regenerated. | Pipeline |
| `wiki/` | `sources/` (one summary per source), `topics/`, `books/` and more, all interlinked. | LLM |
| `index.md`, `log.md` | Catalog of pages, and an append-only history of every operation. | LLM |
| `data/state.db` | SQLite: jobs, de-duplication, retries. | Pipeline |
| `config/` | `privacy.yaml` (cloud policy) and `settings.yaml` (limits, models). | You |
| `AGENTS.md` | The rules the LLM must follow. | You |

---

## 3. Quick start (Windows)

You need: Python 3.11+, an NVIDIA GPU (8 GB is enough) and [Ollama](https://ollama.com).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Install FFmpeg, yt-dlp and ExifTool (for example with winget), then pull the models:
ollama pull qwen3:8b
ollama pull qwen3-vl:8b
ollama pull embeddinggemma

copy .env.example .env
```

Edit `.env`:
- `TELEGRAM_BOT_TOKEN`: create a bot with @BotFather in Telegram.
- `TELEGRAM_ALLOWED_USER_IDS`: your numeric Telegram user ID (for example from @userinfobot). The bot **refuses to start** with an empty list.
- `LLM_PROVIDER=local` (the safe default). Leave cloud keys empty unless you need them.

Open the folder as a vault in **Obsidian** to browse `wiki/`.

---

## 4. Daily use

### 4.1 Talk to the Telegram bot

Start it: `python -m scripts.app bot` (keep the window open; Ollama must be running).

**Just type. No commands are needed.**

| You send | The bot does |
|---|---|
| `What do I know about agentic RAG?` | Answers from the wiki with sources and uncertainty |
| `remember: renew the domain in March` | Saves a note and files it into the wiki |
| `please read https://example.com/post` | Downloads the article and ingests it (a bare URL works too) |
| A YouTube link (alone or in a sentence) | Fetches the video's subtitles with yt-dlp, stores the timestamped transcript in `raw/youtube/` and ingests it; the reply shows title, channel, length and whether the subtitles were manual or auto-generated |
| A PDF, document, audio, video, voice note | Saves to `raw/telegram/`, transcribes/extracts, ingests |
| A photo, or several photos as an album | Describes the images and ingests them as one source |
| A forwarded message | Saves it as a note with the original author |
| Something unclear | Asks: **Answer it** or **Save as note** |

Slash commands still work when you want to be explicit:

| Command | Purpose |
|---|---|
| `/ask <question>` / `/compare <question>` | Answer, or compare positions across pages |
| `/search <words>` | List matching wiki pages (hybrid keyword + meaning search) |
| `/lint` | Wiki health check: broken links, orphan pages, pages without a source, open contradictions |
| `/link` | Suggest missing links between related topic/concept pages (by embedding similarity); nothing changes until you press a **Link N** button |
| `/summarize <title>` | Show a source's stored summary (no model call) |
| `/ingest <text or URL>` | Force-save a note or URL |
| `/ingest_local raw/<folder>/<file>` | For files over Telegram's 20 MB limit that you copied into `raw/` yourself |
| `/status [id]`, `/retry <id>`, `/cancel <id>` | Inspect and control jobs |
| `/provider`, `/privacy` | Show or change the model provider / privacy class for this chat |

### 4.2 Add sources from the PC

```powershell
# put the file in the right raw/ folder first, e.g. raw/books/, raw/videos/, raw/articles/
python -m scripts.app ingest "raw/articles/my-article.md"
```

For web articles, install **Obsidian Web Clipper**, import `config/web-clipper/article.json`
(see `config/web-clipper/README.md`), clip into `raw/articles/`, then run the command above.
Clips are `visibility: private` by default, so they stay local.

**YouTube tutorials** (needs `yt-dlp` on PATH):

```powershell
python -m scripts.app youtube "https://www.youtube.com/watch?v=<id>"
```

This stores `raw/youtube/<title>-<id>.md` (subtitles with `<!-- t: MM:SS -->` markers, so the wiki
can cite `(t. MM:SS)`) and ingests it; running it again reports "Already ingested". Subtitle
languages come from `youtube.subtitle_langs` in `config/settings.yaml`; manual subtitles are
preferred over auto-generated ones. Videos without subtitles, private or age-restricted videos fail
with a clear message (no cookies are used, and audio is not downloaded). YouTube changes often: when
captures start failing, update the tool with `winget upgrade yt-dlp.yt-dlp`. Playlists are not supported.

**Many sources at once** (`batch`):

```powershell
# urls.txt: one URL per line (YouTube and articles mixed; blank lines and # comments are ignored)
python -m scripts.app batch urls.txt
python -m scripts.app batch raw/articles          # every new file in a raw/ folder (--recursive for subfolders)
python -m scripts.app batch urls.txt --dry-run    # only list what would be processed
```

Items run one at a time. One failure never stops the rest; the summary lists the counts, failed
URLs are saved to `urls.txt.failed.txt` (the original list is untouched), and rerunning is safe
because already-ingested sources are skipped as duplicates.

**Automatically** (`watch`):

```powershell
python -m scripts.app watch                       # scan every 30 s (--interval N, --folders articles books)
```

It ingests new files in `raw/articles/` (for example Web Clipper clips) and URL lists dropped into
`inbox/pending/*.txt`. A finished list moves to `inbox/processed/`; if some URLs failed, only those
stay in the list that moves to `inbox/failed/` (move it back to `pending/` to retry). Files still
being written are skipped, and a file that failed is not retried until you edit it or restart. If
Ollama is down the scan stops and tries again on the next round. To start it at logon, create a
Windows Task Scheduler task that runs `.venv\Scripts\python.exe -m scripts.app watch` with the
vault folder as the start-in directory.

### 4.3 Read and explore in Obsidian

- Start at `index.md`, or browse `wiki/topics/`.
- Each topic page links to the source summaries that support it. Each source summary records the
  original file or URL, capture date, author, content hash, privacy class, model used and the
  path to the transcript.
- Use the **graph view** to see how topics from different sources connect.
- `log.md` shows exactly what was added or changed and when.

---

## 5. Safety and privacy

- **Allowlist.** Only the Telegram user IDs in `.env` are served; everyone else is silently ignored.
  Group chats are ignored.
- **Cloud is opt-in per class.** Only `public` sources may use a cloud provider. Notes, voice,
  photos, books and videos are local-only and a cloud request is *blocked*, not silently re-routed.
  The classifier for plain Telegram text is also local-only.
- **Source content is data, not instructions.** Text inside documents or messages cannot trigger
  actions. No arbitrary shell, and file paths are restricted to `raw/`.
- **No secrets in logs.** Tokens and source text are not logged; replies are redacted.
- **Nothing is deleted automatically.** Raw sources are immutable; deletion needs explicit approval.
- Do not send passwords, keys or identity documents through Telegram. Telegram itself can read
  what you send.

---

## 6. Development

```powershell
pytest -m "not integration"     # unit tests, no Ollama needed
pytest                          # includes live tests that need Ollama running
ruff check scripts tests
```

Code map: `scripts/extractors/` (per-format extraction), `scripts/wiki/` (ingest, topic
integration, index), `scripts/providers/` (Ollama, OpenAI-compatible, privacy router),
`scripts/telegram/` (bot, handlers, intent classifier, jobs, query). `plan.md` holds the original
design; `AGENTS.md` holds the rules the LLM follows.

## 7. Known limits and roadmap

- Search is hybrid: keyword matching blended with local `embeddinggemma` embeddings, so a paraphrased
  question still finds the right page. If Ollama is down it falls back to keywords only. The
  brute-force similarity is fine for hundreds of pages; a dedicated index (QMD) is the next step
  for thousands.
- `/lint` reports problems but never edits pages (`python -m scripts.app lint` runs it from the PC).
- `/link` suggests links from page-embedding similarity (`link.min_similarity` in
  `config/settings.yaml`) and only writes after you approve a pair. It needs Ollama's embedding model.
- Quality depends on an 8B local model. `/ask` and `/compare` show verified quotes as *Evidence* and a
  *Verification* line. The check is textual: it proves the quote exists in the cited page, not that the
  answer interprets it correctly, so important claims should still be checked against the source.

### Planned: faster, conversational bot (not started)

Problem: the bot is slow and answers each message in isolation. The 8 GB RTX 3050 runs `qwen3:8b`
with a 4096-token context, a 30 s `keep_alive` and two model calls per question.

- Switch the text model to Qwen3.5-9B, text-only Q4_K_M
  (`ollama pull hf.co/unsloth/Qwen3.5-9B-GGUF:Q4_K_M`; the official `qwen3.5:9b` tag bundles a
  ~1.4 GB vision encoder that barely fits on 8 GB). Set `OLLAMA_LOCAL_TEXT_MODEL` in `.env`.
- Merge the question-or-note classifier and the answer into one model call.
- Raise `keep_alive` (about 30 m) and the Ollama context (8192), keeping the model fully on the GPU.
- Keep the last few turns per chat so follow-up questions work, and use them when searching the wiki.
- Answer in natural language with sources underneath, instead of the fixed Answer / Uncertainty /
  Evidence template. Decide the reply language (Serbian / English).

