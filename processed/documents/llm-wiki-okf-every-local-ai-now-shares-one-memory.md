---
raw_path: raw/youtube/llm-wiki-okf-every-local-ai-now-shares-one-memory-9ciGYHHOLyU.md
content_hash: 15d8f79032cb58809220cbe1f1a7ab56e8277ec0adc7df88491fc20ee43b2eec
title: LLM Wiki + OKF Every Local AI Now Shares ONE Memory
---

<!-- t: 00:00 -->

So, you set up your local AI. It runs without breaking a sweat, and every single session you feed it the same context again, who you are, what you are building, where things live, every time, from scratch. So, you think, "Fine, I will bolt on a memory system." And that is where it falls apart. Most of them eat too many resources, live in the cloud, or your local model just is not sharp enough to call the right tool at the right moment. And no, rag is not the answer here. I will get to why. Here is

<!-- t: 00:31 -->

the real problem. Almost every memory system is built for frontier models, the ones that follow a tool spec even when you hand them half-baked instructions. Andre Karpathy floated the idea of an LLM wiki. Google standardized something close with OK F, but asking a regular local model to follow that spec to the letter, while also doing the actual job you gave it, is a huge ask. You are diluting its intelligence across too many things at once. So, I tried to move the memory burden off the AI and onto the tool itself. One dead simple tool

<!-- t: 01:01 -->

built on Karpathy's LLM wiki and Google's OK F. And spoiler, it did not go as smoothly as I thought. So, did it work? What broke when I ran it on my own local stack? And can this actually become permanent memory for a local AI setup? Let's find out. First, why not just use rag? Rag is great when your knowledge base is basically fixed, terabytes that barely change, and you want fast answers. But the intelligence of the model is never used during retrieval. It is vector math similarity matching. That is the trade you make for

<!-- t: 01:33 -->

fast lookups out of huge data. A text-based LLM wiki is different. It behaves like actual memory. It reads one file, and from there another, following links until it lands on the exact thing you need. And we are not storing terabytes. We are storing personal context, the stuff the AI decides is worth remembering. That is constantly changing. So, you do not want to re-chunk and re-embed everything every time one fact updates. If you have ever used a coding agent, you know this works. It follows breadcrumbs through a

<!-- t: 02:04 -->

code base like a detective. My first attempt was the obvious one. A skill file that embeds the OKF spec plus instructions telling the AI where the root of the memory folder is. It kind of worked and it kind of did not. The model ignored the root path, created the folder in the wrong place, and forgot to update the index. The concept is fine when you have a Claude Opus level model. A local model just cannot follow instructions with that precision. So, is it over? Not so fast. We just have to get more creative. We solved this in real life a long time ago. We store

<!-- t: 02:35 -->

human knowledge in libraries and every library has a librarian. You ask a question, the librarian finds it. You have no idea what index the place uses. You do not need to. That is the shape we use. A library that stores the memories and a librarian agent that takes a query, finds the answer, and hands it back. When new knowledge comes in, the librarian files it away so it turns up next time. In technical terms, memory indexed at every level, an index file the model can walk, and links between the files so it jumps to the right

<!-- t: 03:06 -->

section. And the system is deterministic. The rules are fixed. It only calls the model when it genuinely has to make a decision, so we never drift off the spec. I also added a web UI to talk to the librarian directly and a graph visualizer of how the memories link. Because if it is easy to visualize, it is easy to debug. Now, I need my other AI systems to plug in and use this as their memory layer. That comes down to a handful of MCP tools. Query gives the librarian read tools only. Update memory adds edit, so a stale fact gets fixed. Add memory adds

<!-- t: 03:38 -->

write, so anything worth keeping folds into an existing file or becomes a new one. And because the librarian handles all of that, I never bloat my actual agents with the OKF spec or a pile of memory rules. The librarian is an agent, so it needs a brain. It connects to the same llama.cpp server everything else in my stack already uses, auto discovers whatever model is loaded, sits behind llama swap two, and prefers it. So, a memory query never triggers a swap. Think about that. The harness, the memory, and the model.

<!-- t: 04:10 -->

The whole loop runs on my own box. No cloud API anywhere in the chain. This thing is truly local. Okay, on paper it was done. Then I plugged the real client model in over MCP, and that is exactly where it broke. It had a kind of amnesia it did not know it had. All the client could see was the tool names, query, add, update, status. So, when you asked it something, it answered straight from its own head. It never checked the memory first because it had no idea it held anything useful. And the irony is

<!-- t: 04:42 -->

the internal agent was fine the whole time. We had been feeding it an overview of the knowledge base in its system prompt. It was the client model on the other end of the wire flying blind. So, the fix was to give it a reason to look first. The moment a session connects, we generate a seed memory, a small live summary of what is in the base, and push it through the two channels that reach the client at startup. The MCP instructions field and the description of the query tool. Now, the model opens every session already knowing there is a segment on billing, one on people, one

<!-- t: 05:13 -->

on infrastructure. It stops guessing and starts querying. And we made the seed list what each concept is about, not file names, because your question is far more likely to match 100 requests per minute than a file called rate limits.md. Once it was reliably writing to memory, a subtler problem showed up. It treated memory like a junk drawer. Every new fact became its own file. I tell it, I live in Hyderabad, and it spins up a standalone Hyderabad file disconnected from the profile about me that already exists. The memory grew,

<!-- t: 05:44 -->

but none of it connected. A pile of nodes, not knowledge. So, I gave it two rules. First, enrich before you create. Search for the concept this fact belongs to, and if it is just an attribute of something that exists, patch it in. Do not spawn a new file. Second, link both ways. When it genuinely is a new thing, create the concept, then patch the related ones, too. So, my profile says runs the channel, and the channel says created by me. One honest note on the model. I first tried this with Gemma,

<!-- t: 06:14 -->

the 12B. Mechanically, it was fine, but on the agentic side, the decisions about what to enrich and what to link, it kept getting wrong. So, I went back to my trusty Quinn 3, the 30BA3B, and I watched it on a single consumer GPU do exactly this on its own. Enrich the small facts, wire up the big ones, no hand-holding. By now, the memory was behaving, but I had a feeling I was reinventing a wheel someone smarter had already drawn. So, I went back to what Karpathy actually laid out, and a couple

<!-- t: 06:45 -->

of things were still missing. First, graph health. I added a lint step, fully deterministic, that walks every link and flags orphans, concepts nothing points to, and broken links, pointers that go nowhere. One catch that mattered. The auto-generated index files had to be excluded as link sources, or everything looks connected and orphan detection is useless. Then a maintain tool acts on it, and an internal agent wires the orphans back into the concepts they relate to. Orphans went from one to zero on its own. And contradictions. If I say

<!-- t: 07:17 -->

I moved from Hyderabad to Bangalore, the old version would just append Bangalore and leave Hyderabad sitting in the file. The fix was mechanical. The old fact has to be gone everywhere. Rewrite the whole file if you have to. After that, it cleanly said Bangalore, and only Bangalore. And here's the part that actually landed. Because it all runs through the MCP layer, every agent I use shares the same memory. Whichever tool I am in, it already knows what happened in the other one. My projects, the tool I prefer, the IP of my local box, without

<!-- t: 07:49 -->

me repeating myself every session. It became the memory of my AI, the thing I use every day now. I do not reintroduce myself anymore, but I will be honest. This is not finished, and that is my favorite part. Next up is a cache layer, a hot tier of your most recent memories the agent keeps close. So, it never digs through the whole library just to recall what happened 5 minutes ago. After that, the one I'm excited about, a dreaming feature. When the machine sits idle, the memory reorganizes itself, cleans up, links what should be linked, the way

<!-- t: 08:20 -->

your brain consolidates while you sleep. So, it is getting better at remembering while you are not even using it. Here's what I keep coming back to. A model on your own machine is already great, private, yours. Nothing leaves the box. But, without memory, it is still a stranger. Give it a memory that follows you around, one that lives on your disk as plain markdown you can open and read yourself, and it stops being a generic chatbot. It starts being your AI, one that knows you across every harness. Running it locally is only half of it.

<!-- t: 08:50 -->

The other half is owning what it knows about you. We took back the model, the hardware, the privacy. Memory is the next thing to take back. The whole project is open, built on Karpathy's LLM Wiki and Google's OKR spec. Links in the description. Clone it, plug it into your setup, and give your local AI a memory. If you build something on top of it or want to see a feature in it, tell me in the comments, and I will see you in the next one.
