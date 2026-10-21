---
raw_path: raw/articles/reverse-engineer-anything-rea-can-ai-really-crack-closed-cod-bbad2ccb.md
content_hash: 1f28bf5b392d7c6a18c22c24aa62a4ef08d494de1de07cdd3f1f8e1d3d8901bc
title: 'Reverse Engineer Anything (REA): Can AI Really Crack Closed Code?'
---

Every developer hits this wall eventually. A feature behaves in a way you can’t explain, and the code behind it is locked away. No source. No docs. Just a compiled binary or a wall of minified JavaScript.

Figuring it out the traditional way means hours in a disassembler, specialist tools like Ghidra or IDA, and a skill set most developers never had time to learn. So most people guess, work around it, or give up.

REA (Reverse Engineer Anything) is built to remove that wall. It’s an open-source MCP server that lets AI coding agents investigate native binaries, Electron apps, Android APKs, .NET assemblies, websites and firmware, all from plain-language instructions. You ask how something works. The agent digs in and shows you the evidence.

But can you trust what it tells you? To find out, we predicted how Obsidian’s quick-switcher ranks search results before letting the agent inspect a single line. In this article, we explore REA’s setup, real-world accuracy, blind spots, and the time and token cost of reverse engineering with AI.

REA is an MCP server that connects to your coding agent and exposes about twenty categories of analysis target. The framing most coverage gets wrong is that REA is mostly a **coordinator**, not a decompiler. Miss that and you will install it, point it at a binary, and wonder why nothing happens.

**Key features**

Installation is one command, assuming Node 22 or newer:

`npx rea-agents setup`
It asks which agents to configure, shows the proposed config changes, backs up what it replaces, and registers the MCP server. Restart your agent afterwards. Claude Code, Codex, Cursor, Gemini CLI and Grok Build are supported out of the box.

What you need beyond that depends entirely on your target:

| Target | What you need beyond REA | 
|---|---|
| JavaScript and Electron | Nothing. Node and npm only | 
| .NET assemblies | Nothing. Static inspection only | 
| Go and Rust binaries | Nothing. Metadata is read from the binary | 
| Native binaries | Hopper, Ghidra or IDA, installed and licensed by you | 
| Android APKs | Headless JADX plus a full JDK | 
| Websites | A Chrome-family browser | 
| Firmware, packet captures, crash dumps | Varies, several are Linux-only | 

Everything in this article runs on the top half of that table, so it is reproducible with no paid tooling.

One caution before installing. REA’s README warns that a similar repository name or a copied README does not make a download official, and names morluto/rea, rea.tools and the rea-agents npm package as the real sources. We checked the publisher first: the package is published through GitHub Actions trusted publishing, has 32 released versions, and the repository field matches. Given that setup registers a server which then runs analysis tools locally, this check is worth thirty seconds.

Our target was Obsidian 1.14.4 on macOS, and the question was how its quick-switcher ranks fuzzy filename matches.

Before installing anything, we spent fifteen minutes typing into the search box. We built a throwaway vault of filenames engineered to compete on different match qualities, then recorded the rankings. This date-stamped record is what makes the rest of the article a test rather than a demo.

| Rank | File | Match index | At word boundary | 
|---|---|---|---|
| 1 | graph-db-benchmarks | 0 | yes | 
| 2 | graphql-schema-notes | 0 | yes | 
| 3 | graphql-gateway-design | 0 | yes | 
| 4 | graph-analysis-of-distributed-systems-and-queues | 0 | yes | 
| 5 | legacy-graph-queries | 7 | yes | 
| 6 | grpc-vs-graphql | 8 | yes | 
| 7 | a-b-c-d-e-f-g-h-i-graph | 18 | yes | 
| 8 | zgraph | 1 | no | 
| 9 | xgraphql-adapter | 1 | no | 
| 10 | grand-architecture-proposal-handbook | scattered | n/a | 

Two of those files were written specifically to break a hypothesis. `a-b-c-d-e-f-g-h-i-graph` matches eighteen characters in and is four times longer than `zgraph`, yet it ranks six places higher. Whatever the algorithm weights, starting a word beats starting early.

The last row matters too. `grand-architecture-proposal-handbook` matches g, r, a, p, h scattered across word starts, which confirms subsequence matching exists and ranks below every contiguous match.

A tiered sort, in descending priority:

All ten rows fit. We were fairly pleased with it.

This query produced fourteen results, almost all scattered matches, and three rows killed the model outright.

| Rank | File | g index | q index | Boundaries hit | 
|---|---|---|---|---|
| 2 | goal-q3-planning | 0 | 5 | both | 
| 3 | git-log-quirks | 0 | 8 | both | 
| 5 | graphql-schema-notes | 0 | 5 | g only | 
| 6 | graphql-gateway-design | 0 | 5 | g only | 
| 7 | general-ledger-questions | 0 | 15 | both | 
| 11 | legacy-graph-queries | 2 | 12 | q only | 
| 12 | grpc-vs-graphql | 0 | 13 | g only | 
| 14 | graph-analysis-…-queues | 0 | 41 | both | 

Ranks 5 and 6 hit one boundary and beat rank 7, which hits two, so boundary count is not the top key. `grpc-vs-graphql` starts its match at index 0 on a word boundary yet lands at rank 12, below a file whose `g` is buried mid-word, so first-character position is not the top key either. And the last row has both characters on clean word starts but finishes last, because its `q` sits at index 41.

Not a tiered sort at all, but a weighted numeric score where every matched character contributes: a large penalty for fragmentation, a per-character penalty for landing mid-word, and a penalty growing with position.

Two rows bracket the trade-off. Rank 3 beats rank 5 despite its `q` sitting three characters later, so a boundary is worth more than roughly three positions. Rank 6 beats rank 7 despite one fewer boundary and a `q` ten characters earlier, so a boundary is worth less than roughly ten.

**A boundary is worth between 3 and 10 positions.** That is a falsifiable quantitative prediction, derived entirely from the outside in fifteen minutes.

**The prompt**

We gave no architectural hints, named no files, and pointed at nothing specific:

```
Obsidian is installed at /Applications/Obsidian.app. Work out how its
quick-switcher scores and ranks fuzzy matches. Show me the evidence for
each step, and tell me what you could not determine.
```
The first useful thing the agent did was avoid an obvious trap. `Contents/Resources/` holds both `app.asar` and `obsidian.asar`, and the one named `app.asar` is only a 472KB Electron bootstrap shim. The real application is the 27MB `obsidian.asar`. Extracting it produced a single 3.9MB minified `app.js`.

This is the step that justifies the exercise, and the approach was smarter than brute-force searching.

Obsidian exposes `prepareFuzzySearch` and `fuzzySearch` as public API for plugin authors, so those names survive minification in the export table. The agent searched for them and followed their minified aliases inward: `lx`, `sx`, `hx`, `ux`, `cx`. The public API is a labelled door into unlabelled code.

It then did the check that separates analysis from guesswork. It confirmed that `oie`, the actual `QuickSwitcherModal` class, extends `D5`, the suggestion class whose `getSuggestions` contains that pipeline. Finding plausible-looking scoring code and assuming it is the code that runs is the classic failure mode here, and it verified the inheritance before trusting the trace.

Matching happens in two tiers (`hx`/`ux`, around byte offset 1256510). Tier 1 requires every whitespace-separated token to appear as a literal contiguous substring, searched left to right. If that fails, Tier 2 falls back to character-by-character subsequence matching. If neither tier matches, the file is dropped entirely rather than scored low.

Scoring is a single function, `cx`, around offset 1256690:

```
r  = 0
r -= max(0, fragments - 1)                             // 1.0    per extra fragment
r -= boundaryMisses / 10                                // 0.1    per mid-word character
r -= (lastMatchEnd - firstMatchStart - queryLen) / 100  // 0.01   per character of span
r -= firstMatchStart / 1000                             // 0.001  per character of lateness
r -= targetLen / 10000                                  // 0.0001 per character of filename
```
Zero is the best possible score, everything else negative. The five constants are scaled roughly ten times apart, which makes the sum behave like a lexicographic priority order.

A matched character escapes the boundary penalty if it is the first character of the string, if it is punctuation or CJK, if it is an uppercase letter following a lowercase one (the camelCase hump, so the S in `webSocket` is free), or if it is a lowercase letter following a separator.

Two mechanisms were invisible from outside. A path wrapper at offset 1826030 tries the bare filename first and only falls back to the full path, applying a flat 1.0 penalty when it does, which is why filename matches almost always beat folder-name matches. And files in excluded folders are not dropped but penalised by 10.0, so they surface only when nothing else matches.

| What we predicted from behaviour | Verdict | 
|---|---|
| Contiguity dominates everything | Correct. The 1.0 term, ten times the next | 
| Word boundary outranks position | Correct. 0.1 against 0.001 | 
| Earlier position beats later | Correct, but it is two terms, not one | 
| Shorter filename breaks ties | Correct. The 0.0001 term | 
| The priority order of all four | Correct, in exactly that sequence | 
| A boundary is worth 3 to 10 positions | Correct. It is exactly 10 | 

That last row came from a single pair of files where the two terms almost exactly cancel:

```
graphql-gateway-design:    -1 - 0.1 - 0.05 - 0 - 0.0022 = -1.1522
general-ledger-questions:  -1 - 0   - 0.15 - 0 - 0.0024 = -1.1524
```
One boundary miss costs 0.1. Ten characters of span cost 0.10. The pair is a dead tie decided by two ten-thousandths of a point of filename length, which is why that one ordering pinned the ratio exactly.

**Where the prediction was wrong.** Fragmentation is a count, not a binary: a three-piece match is penalised twice as hard as a two-piece, and our vault contained no three-fragment case to reveal it. And what we called “position” is really two separate terms ten times apart, span and start offset.

The agent did not stop at reading minified code. It extracted the real `cx` and `ux` functions and executed them in Node against constructed inputs:

| Query | Candidate | Score | Why | 
|---|---|---|---|
| dp | zzz/dp.md | -0.01 | one contiguous fragment | 
| dp | Projects/Daily Planning.md | -1.06 | two fragments | 
| ws | WebSocket.md | -1.03 | two fragments, no boundary penalty | 
| ws | workspace.md | -1.14 | two fragments plus one boundary miss | 
| ab | ab-contiguous.md | -0.01 | one fragment | 
| ab | a-b-fragmented.md | -1.02 | two fragments | 

Rows 3 and 4 are the useful pair: same query, same fragment count, and the 0.11 difference is entirely the `camelCase` exemption. We then checked the formula against all twenty-four rankings recorded by hand before the analysis. Every position is predicted correctly.

| Metric | Value | 
|---|---|
| Wall-clock for the investigation | 7 min 8 sec | 
| API time, whole session | 9 min 11 sec | 
| Cost | $1.83 | 
| Fresh input tokens | 1,200 | 
| Output tokens | 36,300 | 
| Cache write | 228,500 | 
| Cache read | 2,900,000 | 

Ninety-seven percent of input came from cache across 31 requests with no misses. That 2.9m cache-read figure is what a long agentic investigation looks like from the inside, and prompt caching is the only reason this costs under two dollars.

One number we are deliberately not quoting is the 18h 45m wall-clock the session reported, because the session sat idle overnight. Wall-clock on an agent session measures when you returned to your desk, not how long the work took.

**It can refuse to start, and that is correct behaviour.** Our first run died on an integrity mismatch: a native module unpacked from the archive no longer matched the hash recorded in the archive header. macOS codesigning rewrites native binaries after the ASAR is built, so the hash goes stale by design. REA offers an override flag, but we verified the signature first with `codesign --verify --deep --strict` and `spctl`, which came back valid, notarized and signed by Dynalist Inc., the company behind Obsidian. Only then did we use the flag. A tool that halts on an ambiguous integrity signal is behaving better than one that quietly analyses possibly-tampered bytes.

**The reported formula had an ambiguity.** The agent wrote the span term as `lastMatchEnd - firstMatchStart + 1 - queryLen`, but every row of its own verification table only reconciles if the end offset is exclusive. The numbers were right and the prose was not. Implementing from the write-up instead of checking it against the table would have shipped an off-by-one.

**The agent layer has its own moving parts.** After finishing, the session fired a stray scheduled wakeup from an earlier call, found nothing to do, and stopped itself. Harmless, but independent of the analysis quality.

**Failure modes that did not bite here but might for you.** Confident wrong call paths, context exhaustion on large bundles, vagueness as the trace goes deeper into minified code, and gaps filled with plausible fiction. The last is the most dangerous because it reads like success, and independent verification is the only reliable defence.

One audience deserves a specific caution. REA will be most attractive to people building fast with AI agents, and that is precisely the group least equipped to catch its failure mode. The value of this tool scales with your ability to check its answers. If the appeal is skipping the understanding step, the failure modes above are about you.

It also does not replace a security researcher. The agent is good at navigation and summarising. Knowing which of fifty findings actually matters is still the expensive skill.

Lowering the effort of reverse engineering does not change what you are permitted to do with it. REA’s stated position is that it exists for lawful research, education, interoperability, software preservation, and analysis of software you own or are authorized to examine.

Three practical consequences. Check the terms of whatever you point it at, because “I installed it” and “I am permitted to analyse it” are different claims. Understanding a feature is not a licence to copy its implementation, and reimplementation deserves a conversation with someone qualified before it ships. And the commercial engines are your responsibility: REA grants no licence for IDA, Hopper or JEB.

**Read more:** Agentic Context Engineering (ACE): Self-Improving Language Models

Seven minutes and $1.83 against an afternoon in devtools is the headline, but it is not what convinced us. What convinced us is that the answer was checkable. We had a model derived from behaviour, the agent produced a formula from code, and the two agreed on everything observable from outside while adding four mechanisms that were not. Had the formula been invented, twenty-four hand-recorded rankings would have caught it.

The transferable lesson is the order, not the tool. Fifteen minutes spent forming a testable prediction before the agent sees anything costs almost nothing and changes what the output is worth. Without it you have a fluent explanation. With it you have a claim that either survived contact with evidence or did not, and you can tell which.

If you want to try REA without committing to a full setup, this runs in about five minutes and needs only Node:

```
npx -y rea-agents@latest analyze-javascript-application \
  /path/to/any/electron/app --json
```
A. No. For JavaScript and .NET it performs static inspection itself, but for native binaries it coordinates Ghidra, Hopper or IDA, which you install and license yourself.

A. Analysis runs locally. However, your agent’s model provider still sees the tool results under its own data policy.

A. The algorithm itself was traced correctly and verified in Node. The written formula contained an ambiguous off-by-one in the span term that only surfaced when checked against its own verification table.

A. $1.83 and 7 minutes 8 seconds of active work, with 97% of input tokens served from cache.

A. It depends on the software’s terms and your jurisdiction. REA’s stated scope is lawful research, interoperability, preservation, and software you own or are authorized to examine. Reimplementing what you learn is a separate question with different legal weight.
