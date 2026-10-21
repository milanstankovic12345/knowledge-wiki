---
title: 'A Practical Guide to Harness Engineering: Building the System Around the Model'
type: source-summary
source_type: article
source_url: https://www.analyticsvidhya.com/blog/2026/10/agent-harness-engineering-guide/
raw_path: raw/articles/A Practical Guide to Harness Engineering Building the System
  Around the Model.md
processed_paths:
- processed/documents/a-practical-guide-to-harness-engineering-building-the-system.md
creator: Janvi Kumari
captured_at: '2026-10-21'
processed_at: '2026-10-21T22:45:19+02:00'
content_hash: 414fa82bdf882832228fbad0713f9137ff3c1d48f8609d82b53b78b063f93910
privacy: personal
llm_provider: ollama-local
llm_model: qwen3:8b
status: active
tags:
- source/article
---

# A Practical Guide to Harness Engineering: Building the System Around the Model

## Summary

The document introduces the concept of harness engineering as a system that enables AI agents to perform tasks effectively by providing context, tools, and checks. It explains that a model alone cannot handle real-world tasks due to limitations like not knowing the project structure, inability to run tests, and lack of memory. The harness addresses these issues by managing the agent's workflow, providing necessary information, and verifying results. The guide outlines six layers of a harness: instructions, context, tools, durable state, orchestration, and verification. It also discusses security and cost considerations, emphasizing the need for sandboxing, least privilege, and limits on steps and resources. The document concludes with a practical example of a mini harness designed to fix a specific bug. The source describes a harness system for managing a coding project with a model that can execute tasks, run tests, and maintain state. It includes a scripted model for offline use and a real model adapter. The source describes a Python implementation of a harness for testing AI agents, focusing on scenarios where an agent must fix a bug in a checkout system. The harness includes a scripted model and a real model (Claude) that interacts with an API. It also outlines how to run tests, handle errors, and improve the harness.

## Main ideas

- Harness engineering is essential for enabling AI agents to perform real-world tasks effectively.
- A harness connects the model to information and tools, manages the task steps, and checks the results.
- The six layers of a harness include instructions, context, tools, durable state, orchestration, and verification.
- Security and cost considerations are critical in harness design, including sandboxing, least privilege, and resource limits.
- The mini harness example demonstrates how these concepts can be applied to fix a specific bug.
- The harness system manages a coding project by executing tasks, running tests, and maintaining state.
- The system includes a scripted model for offline use and a real model adapter for live interaction.
- The harness enforces permissions, limits steps, and ensures tests are run before accepting a finish action.
- A harness is a framework that provides an AI agent with tools, permissions, and checks to perform tasks and verify success.
- The harness includes a scripted model that simulates an agent's actions and a real model (Claude) that interacts with an API.
- The harness runs tests to validate the agent's actions and ensures the agent stays within defined boundaries (e.g., sandboxing).
- The harness can be extended with features like approval steps, compaction, and additional tools.
- Harness engineering differs from prompt engineering by providing a structured environment for the agent to operate within.

## Important claims

- A model alone cannot handle real-world tasks due to limitations like not knowing the project structure, inability to run tests, and lack of memory (p. 1).
- A harness addresses these limitations by providing the necessary information, tools, and checks (p. 1).
- Harness engineering includes the runtime and controls around the model, distinguishing it from prompt and context engineering (p. 2).
- The six layers of a harness are instructions, context, tools, durable state, orchestration, and verification (p. 3).
- Security measures like sandboxing, least privilege, and approval gates are essential to limit the agent's impact (p. 4).
- Cost considerations include step and time limits, token budgets, and retry caps to prevent excessive resource use (p. 4).
- The mini harness example demonstrates how these concepts can be applied to fix a specific bug (p. 5).
- The harness system loads AGENTS.md into the system prompt and clips long tool output (p. 1).
- The tool gate keeps paths inside the workspace and makes tests/ and AGENTS.md read-only (p. 1).
- The verify layer runs tests before accepting a finish action (p. 1).
- The state file saves each step and the final status to .harness/state.json (p. 1).
- The step limit stops the loop after a set number of steps (p. 1).
- The model is swappable, with a scripted model for offline use and a real model adapter (p. 2).
- The harness is implemented in a single file, harness_demo.py (p. 3).
- The offline demo uses only the Python standard library (p. 4).
- The make_workspace function creates a temporary folder with a project, tests, and AGENTS.md (p. 5).
- The tools include list_files, read_file, write_file, run_tests, and finish (p. 6).
- The Harness class manages workspace, model, step limit, and approval function (p. 7).
- Permissions ensure paths stay within the workspace and prevent writing to read-only files (p. 8).
- The clip method trims tool output to a limit and hides the workspace path (p. 9).
- The execute method wraps tools and handles denied or failed actions (p. 10).
- The save_state method writes progress to a JSON file (p. 11).
- The run method is the core loop, asking the model for actions and running them (p. 12).
- The ScriptedModel plays back fixed actions for repeatable offline use (p. 13).
- The harness uses a scripted model to simulate an agent's actions in a test scenario (p. 12).
- The real model (Claude) interacts with an API to make decisions and returns the first tool call (p. 12).
- The harness runs tests to validate the agent's actions and ensures the agent stays within defined boundaries (p. 12).
- The harness includes a step limit to prevent agents from getting stuck in loops (p. 12).
- The harness can be extended with features like approval steps, compaction, and additional tools (p. 12).
- Harness engineering provides a structured environment for the agent to operate within, differing from prompt engineering (p. 12).

## Useful examples

- None extracted.

## Questions raised

- What are the key limitations of a language model when performing real-world tasks?
- How does a harness address these limitations?
- What are the six layers of a harness, and what do they do?
- What security measures are recommended for harness design?
- How do cost considerations influence harness engineering?
- What is the purpose of the mini harness example in the document?
- What is the purpose of the harness system?
- How does the harness enforce permissions?
- What is the role of the ScriptedModel?
- How does the harness handle test failures?
- What is the function of the state file?
- What is a harness and how does it differ from a prompt?
- How does the harness ensure the agent stays within defined boundaries?
- What are some ways to extend the harness?
- What is the purpose of the step limit in the harness?
- How does the harness handle errors and invalid actions?

## Contradictions

- None recorded.

## Related wiki pages

- [[topics/harness-engineering]]
- [[topics/agent-harness]]
- [[topics/prompt-engineering]]
- [[topics/context-engineering]]
- [[topics/six-layers-of-a-harness]]

## Processing notes

- Summary generated by `ollama-local` / `qwen3:8b`; verify against the raw source.
- Extraction: `processed/documents/a-practical-guide-to-harness-engineering-building-the-system.md` (reproducible, not LLM-written).

## Provenance

- Original: https://www.analyticsvidhya.com/blog/2026/10/agent-harness-engineering-guide/
- Raw file: `raw/articles/A Practical Guide to Harness Engineering Building the System Around the Model.md`
- SHA-256: `414fa82bdf882832228fbad0713f9137ff3c1d48f8609d82b53b78b063f93910`
- Captured: 2026-10-21
- Author: Janvi Kumari
- Privacy: personal
