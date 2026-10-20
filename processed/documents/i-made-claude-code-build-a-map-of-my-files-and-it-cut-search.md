---
raw_path: raw/articles/i-made-claude-code-build-a-map-of-my-files-and-it-cut-search-4608af51.md
content_hash: abf4d3fc1cf883f29b2b6be0d226a235a61939f70691968743c3837e78c94daa
title: I made Claude Code build a map of my files, and it cut search times by 96%
---

Whether it's my digital life or my wardrobe we're talking about, I've always been terrible at keeping things organized. Every once in a while, I'll get a random burst of motivation at 3 AM and convince myself that this is finally the night I'm going to get my life together. I'll start sorting through everything, creating folders, renaming files, and putting things where they actually belong. But, as you can probably imagine, that motivation rarely lasts long enough for me to finish what I started.

My computer is probably the best example of this. Between university assignments, work-related documents, screenshots for articles, and the countless random files I've accumulated over the years, finding something I saved even a few weeks ago can feel like searching for a needle in a haystack. Frankly, Finder's built-in search isn't always much help, either. It's decent when you know exactly what a file is called, but not so much when all you can remember is what the file was about.

So, instead of waiting for another 3 AM burst of motivation to finally get my files in order or looking for a Finder alternative, I decided to try something different. I asked Claude Code to write a README for every important folder on my computer. While I wasn't expecting much, I certainly wasn't expecting it to cut the time it took to find one of my files by a whopping 96%.

## Claude Code turned my computer into its own personal knowledge base

### Turns out, my computer needed a tour guide

The idea was pretty simple: I'd let Claude explore my existing files and folders, figure out what everything was, and create a reference system it could consult whenever I needed to find something.

That's where README files come in. If you've ever downloaded an open-source project from GitHub, you've probably come across a README.md file before. They're essentially Markdown documents that explain what a project contains, how it works, and other information someone might need to know about it. While they're typically used for software projects, I figured there was no reason I couldn't use them for my own files, too.

Rather than creating a single massive README listing everything on my computer, I wanted Claude to build a hierarchy of them. A master README would act like a table of contents, pointing to smaller READMEs inside important folders, which would then explain what those folders contained. More importantly, I didn't want these documents to simply list filenames. I wanted them to describe what files were actually about, include keywords I'd naturally use when looking for them, and explain relationships between files stored in different places.

So, I opened Claude Code in my home directory and gave it the following prompt:

Claude started by inspecting my home directory and identifying the folders worth exploring. It then launched three parallel agents to examine different parts of my computer: one focused on my Desktop, another on Downloads, and the third on my home-directory projects and Documents.

This exploration turned out to be more involved than I expected. Between college coursework, article screenshots, coding projects, and the random files I'd accumulated over time, Claude had quite a bit to work through. It also found some rather confusing relationships between files.

For instance, some of my database management SQL files were sitting inside a folder named COAL, which is actually the name of my assembly-language course. Exactly the kind of thing that makes finding files on my computer such a nightmare!

Once the exploration was complete, Claude presented a plan detailing which folders deserved their own README files and which could be covered by the master index. Before approving it, I sent one more instruction:

## Claude turned hundreds of messy files into 7 organized READMEs

Claude ultimately created seven README files and one CLAUDE.md file. The main README sat in my home directory and acted as the starting point, with more specialized READMEs covering my Desktop, Downloads, Documents, assembly-language coursework, and a couple of particularly chaotic subdirectories.

The CLAUDE.md file served a different purpose. Rather than describing my files, it told Claude Code how to find them: start with the master README, follow the relevant links to narrower indexes, and verify the actual file before giving me an answer. So, in theory, future Claude Code sessions wouldn't need to search my entire computer every time I asked where something was.

Claude also ran a validation check on the structure it had created. It initially found four issues with the references, fixed them, and eventually reported that all 309 links and filename references resolved correctly. More importantly, it hadn't moved or renamed any of my existing files.

## My first test delivered a ridiculous 96% reduction in search time

### Went from over 4 minutes to just 9 seconds

Now, I obviously wasn't going to let all of Claude's hard work go to waste without putting the system to the test. I began by opening two separate Claude Code sessions, both running the same model, Claude Sonnet 5.5. I also made sure to launch Claude Code in safe mode using the --safe-mode flag, which disables customizations like CLAUDE.md files, skills, hooks, and plugins. This was particularly important because I'd just created a CLAUDE.md file instructing Claude to consult the README hierarchy whenever I asked it to find something, and I didn't want those instructions influencing both sessions.

The idea was to see how much of a difference the READMEs actually made. In the first session, I explicitly instructed Claude to start with the master README in my home directory, follow the relevant READMEs in subdirectories, and verify that the files it found actually existed. In the second session, I told Claude to ignore the READMEs entirely and rely on its usual filesystem search tools instead.

I started by asking both sessions to find an assembly language program I'd written for college that displayed an ATM menu with options for withdrawing and depositing money. Now, the catch here was that I hadn't named the file anything remotely descriptive. It was simply called labtask4.asm, and it was buried inside my DOS folder. So, unless Claude already knew where to look, finding it meant searching through my files and figuring out which program matched my description.

With the README hierarchy, Claude found the correct program in just 9 seconds. It consulted the master README, followed it to the README inside my DOS folder, and used that to identify the exact file. After verifying that the program actually contained the ATM menu I described, it gave me the correct path. All of that took just two shell commands.

Without the READMEs, things went a little differently. Claude started searching for assembly files across my home directory, and that initial search alone took nearly three minutes. It even ended up checking an unrelated assembly program before eventually finding the right one. By the time it had finished searching and verifying the result, 4 minutes and 20 seconds had passed.

Both sessions ultimately found the exact same file, but one did it in 9 seconds while the other took 260 seconds. That's a whopping 96.5% reduction in the displayed time it took Claude to find the file, all because the first session had a map telling it where to look.

In all the other tests I did, the README hierarchy continued to make a noticeable difference, although the results weren't quite as dramatic as the first one. Across the eight tests I ran, the session using READMEs finished faster in seven and tied with the other in one. Adding up the displayed completion times, the README-guided searches took just 79 seconds, compared to 382 seconds without the indexes. That's roughly an 79% reduction in total search time, although the unusually slow first test accounted for a large portion of that difference.

What surprised me most, though, wasn't necessarily the speed improvement. It was how much less searching Claude had to do. Instead of repeatedly scanning directories and trying to figure out what vaguely named files contained, it could consult a short description, narrow down where to look, and go straight to verifying the relevant files. That's exactly what I'd hoped to achieve when I started this experiment.

### There's still one problem I haven't figured out

I'm still working on figuring out the best way to maintain this system over time, though. After all, it's only a matter of time before I accumulate another few hundred files, create even more ridiculously named folders, and render parts of the READMEs outdated.

That said, even in its current state, I'm genuinely impressed with how well this experiment turned out. I haven't magically become any better at organizing my files, and my Desktop is probably going to look like a complete disaster again in a few weeks. But at least now, there's a much better chance I'll actually be able to find what I'm looking for.
