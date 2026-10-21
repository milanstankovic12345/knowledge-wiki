---
raw_path: raw/articles/Every Local AI I Run Now Shares ONE Memory  (LLM Wiki + OKF).md
content_hash: 46179e4f542dfc5d3702220cbd0838faa60e431f7ebf3c0024e61838555a98be
title: Every Local AI I Run Now Shares ONE Memory | (LLM Wiki + OKF)
---

# Every Local AI I Run Now Shares ONE Memory | (LLM Wiki + OKF)

## Metadata

- URL: https://www.youtube.com/watch?v=IwN-eK1s8og
- Author: Codacus
- Captured: 2026-10-21T22:41:44+02:00

## Content

I gave every local AI I run ONE shared, permanent memory — teach something to one agent, and every other agent already knows it. No vector database, no cloud API, no re-embedding. Just a folder of markdown files, a "librarian" agent, and MCP.  
  
It's built on Andrej Karpathy's LLM-wiki idea and Google's OKF (Open Knowledge Format) spec, and the whole loop runs on my own box: the harness, the memory, AND the model (same llama.cpp server everything else uses).  
  
In this video I build understory, a drop-in memory layer for ANY local AI setup. AnythingLLM, llama.cpp web UI, coding agents, anything that speaks MCP, and I show you exactly what broke along the way: the cold-start problem (the AI never thought to check its own memory), the junk-drawer problem (every fact became an orphan file), and how a deterministic harness makes it all work on a small local model. Deterministic rules, the LLM only for decisions.  
  
🌱 understory (free & open source): https://github.com/thecodacus/understory  
Karpathy's LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f  
Google's OKF spec: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md  
  
⏱️ CHAPTERS  
0:00 Your local AI has amnesia  
1:25 Why RAG is NOT the answer (memory ≠ vector DB)  
3:04 The naive fix: a skill file (and how it broke)  
3:50 Every library has a librarian — the architecture  
5:26 Meet understory: watch the memory grow  
5:59 Plug it into anything: the 3 MCP tools  
6:53 Truly local, it runs on the same llama.cpp  
7:44 Challenge 1: it forgot to remember (cold start)  
9:19 Challenge 2: the junk drawer (linking memories)  
11:01 Fixing the final gaps (lint, maintain, contradictions)  
12:34 One memory, every agent  
12:58 My Thoughts + the roadmap  
  
THE STACK  
• Memory: plain markdown files (Google's OKF spec) — no database, every "memory" is a file you can read, edit, and git-diff  
• Agent: TypeScript + Vercel AI SDK v5 tool loop (search / read / write / patch / link)  
• Protocol: MCP server (streamable HTTP + stdio) — works with Claude, llama.cpp webui, any MCP client  
• Inference: llama.cpp llama-server on my homelab GPU (also supports Anthropic / OpenRouter)  
• UI: React + Vite + Tailwind, d3-force for the memory graph + query-path replay  
• Server: Node + Express, single Docker container (image on GHCR)  
  
  
Every byte of your AI's memory stays on your disk, readable in any text editor, diffable in git. We took back the model, the hardware, and the privacy — memory is the next thing to take back.  
  
🔔 Subscribe if you're building a local AI stack you actually own: https://youtube.com/@Codacus?sub\_confirmation=1  
  
What should your AI remember first? Tell me in the comments.  
  
#localai #llamacpp #edgeai #aimemory #llm #obsidian #okf
