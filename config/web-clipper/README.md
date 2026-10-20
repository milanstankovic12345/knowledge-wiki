# Obsidian Web Clipper: Article template

One-time manual setup (the extension cannot be installed from this repo):

1. Install the official Obsidian Web Clipper in your browser.
2. Open its settings, choose **Templates -> Import**, and select `config/web-clipper/article.json`.
3. Check that the template's vault is `knowledge-wiki` and its folder is `raw/articles`.
4. Clip an article, then ingest it:
   `python -m scripts.app ingest "raw/articles/<clip>.md"`

The template sets `visibility: private`, so clips are classified `personal` and stay local-only.
To allow cloud processing of one clip, change `visibility` to `public` before ingesting.
`status: pending` is informational; ingest state lives in `data/state.db`, never in `raw/`.
