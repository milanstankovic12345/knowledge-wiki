---
title: Every Local AI I Run Now Shares ONE Memory | (LLM Wiki + OKF)
type: source-summary
source_type: article
source_url: https://www.youtube.com/watch?v=IwN-eK1s8og
raw_path: raw/articles/Every Local AI I Run Now Shares ONE Memory  (LLM Wiki + OKF)
  1.md
processed_paths:
- processed/documents/every-local-ai-i-run-now-shares-one-memory-llm-wiki-okf.md
creator: Codacus
captured_at: '2026-10-21'
processed_at: '2026-10-21T22:45:54+02:00'
content_hash: 10b618689f3227e8ad59a8a840df91c27908435c0c917519ea4c1a0ce36a9ff5
privacy: personal
llm_provider: ollama-local
llm_model: qwen3:8b
status: active
tags:
- source/article
---

# Every Local AI I Run Now Shares ONE Memory | (LLM Wiki + OKF)

## Summary

The source discusses a method for creating a shared memory system for local AI agents using markdown files and a 'librarian' agent. It references Andrej Karpathy's LLM-wiki idea and Google's OKF format. The system is built on llama.cpp and runs locally without cloud dependencies. Challenges include cold-start issues and memory management, which are addressed through deterministic rules and a memory graph visualization. The text discusses the development of a personal AI memory system, addressing issues like unconnected data, contradictions, and orphaned concepts. It outlines strategies for enriching and linking information, using tools like a lint step and maintain tool to ensure data integrity. The system allows multiple AI agents to share a unified memory, enhancing personalization and functionality. The author plans to add features like a cache layer and a dreaming mode for memory consolidation, emphasizing the importance of local, private AI memory for creating a personal AI assistant.

## Main ideas

- Shared memory for local AI agents using markdown files and a librarian agent.
- The system is based on Karpathy's LLM-wiki and Google's OKF format.
- The system runs locally on llama.cpp without cloud dependencies.
- Challenges include cold-start issues and memory management, which are addressed through deterministic rules and a memory graph visualization.
- The AI memory system initially faced issues with unconnected data and orphaned concepts.
- Strategies like enriching before creating and linking both ways were implemented to improve data organization.
- A lint tool was introduced to detect and fix orphans and broken links, ensuring data integrity.
- Contradictions were resolved by systematically removing old facts and rewriting the data.
- The system allows multiple AI agents to share a unified memory, enhancing personalization and cross-tool functionality.
- Future plans include adding a cache layer for recent memories and a dreaming mode for memory consolidation.
- The author emphasizes the importance of local, private AI memory for creating a personal AI assistant.

## Important claims

- Every local AI I run now shares one memory (p. 1).
- The system is built on Karpathy's LLM-wiki idea and Google's OKF spec (p. 1).
- The system runs on the same llama.cpp server (p. 1).
- The cold-start problem occurs when the AI doesn't check its memory (p. 7:44).
- The junk-drawer problem occurs when facts become orphan files (p. 9:19).
- The system uses deterministic rules and the LLM only for decisions (p. 11:01).
- The system uses a memory graph visualization (p. 5:26).
- The system uses MCP tools for querying, updating, and adding memory (p. 5:59).
- The AI system initially treated memory like a junk drawer, creating disconnected files for each fact (p. 9:18).
- The system was improved by implementing rules to enrich existing concepts before creating new ones and linking both ways (p. 10:06).
- A lint tool was added to detect orphans and broken links, ensuring data integrity (p. 11:15).
- Contradictions were resolved by removing old facts and rewriting the data (p. 12:21).
- The system allows multiple AI agents to share a unified memory, enhancing personalization and cross-tool functionality (p. 12:34).
- Future plans include adding a cache layer for recent memories and a dreaming mode for memory consolidation (p. 13:41).
- The author emphasizes the importance of local, private AI memory for creating a personal AI assistant (p. 14:41).

## Useful examples

- None extracted.

## Questions raised

- What should your AI remember first?
- How does the system handle memory management?
- What are the challenges of using a shared memory system for local AI agents?
- How does the system ensure that the AI checks its memory?
- How does the AI memory system handle contradictions in data?
- What are the key strategies used to improve data organization in the memory system?
- How does the system ensure data integrity through the lint tool?
- What future features are planned for the AI memory system?
- What is the significance of local, private AI memory in creating a personal AI assistant?

## Contradictions

- None recorded.

## Related wiki pages

- [[topics/shared-memory]]
- [[topics/librarian-agent]]
- [[topics/llm-wiki]]
- [[topics/okf-format]]
- [[topics/cold-start-problem]]

## Processing notes

- Summary generated by `ollama-local` / `qwen3:8b`; verify against the raw source.
- Extraction: `processed/documents/every-local-ai-i-run-now-shares-one-memory-llm-wiki-okf.md` (reproducible, not LLM-written).

## Provenance

- Original: https://www.youtube.com/watch?v=IwN-eK1s8og
- Raw file: `raw/articles/Every Local AI I Run Now Shares ONE Memory  (LLM Wiki + OKF) 1.md`
- SHA-256: `10b618689f3227e8ad59a8a840df91c27908435c0c917519ea4c1a0ce36a9ff5`
- Captured: 2026-10-21
- Author: Codacus
- Privacy: personal
