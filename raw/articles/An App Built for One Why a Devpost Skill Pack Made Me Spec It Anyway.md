---
title: "An App Built for One: Why a Devpost Skill Pack Made Me Spec It Anyway"
type: "raw-source"
source_type: "article"
source_url: "https://dev.to/earlgreyhot1701d/an-app-built-for-one-why-a-devpost-skill-pack-made-me-spec-it-anyway-knh"
author:
  - "Earl Grey"
captured_at: 2026-10-20
status: "pending"
visibility: "private"
tags:
  - "source/article"
---
# An App Built for One: Why a Devpost Skill Pack Made Me Spec It Anyway

## Metadata

- URL: https://dev.to/earlgreyhot1701d/an-app-built-for-one-why-a-devpost-skill-pack-made-me-spec-it-anyway-knh
- Author: Earl Grey
- Captured: 2026-10-20T12:50:47+02:00

## Content

*My wife lost her yellow book. So I built her an app.*

> **TL;DR:** Cuenta is a small app for my wife's wholesale bakery: count what's left on each cafe's shelf, build the delivery, print and email her branded invoice, and see who owes what. I built it for Devpost's [Build With AI: Basics](https://learn-ai-basics.devpost.com/) hackathon with their skill pack, which interviews you and writes the plan from your answers. The plan caught real problems before any code existed. It also carried one wrong guess all the way to the end, and only using the app caught it.

Last week E. lost her yellow book.

The yellow book is sacred. It holds all the secrets of her one-person wholesale bakery: her shelf counts for every cafe she delivers to, and her delivery numbers. The counts tell her what to bake. The delivery numbers become her invoices. When the book went missing, all of that went with it, and there was no backup anywhere.

We found it, eventually. (Note to self: Always double check under the front seat of the car.) But I kept thinking about how much of a small business can live in one notebook.

E. runs La Condesa Baking Company, a wholesale bakery in with four cafe accounts. Until now she counted products on paper, filled in invoice forms by hand, did the math by hand, and kept track of who owed her in her head. Net 30, paid by ACH.

So when [Devpost](https://devpost.com/) opened [Build With AI: Basics](https://learn-ai-basics.devpost.com/), a hackathon where you build a new project from an empty folder using their skill pack, I knew what I wanted to make. Something for someone I care about. And a chance to see if a guided process would help me avoid some of my usual costly mistakes.

Cuenta is Spanish for "count" and for "the bill." E. picked the name.

A few days earlier I'd built a tip calculator with Cursor in eight minutes, and [ended that post](https://dev.to/earlgreyhot1701d/eight-minutes-to-live-was-it-cursor-or-was-it-the-spec-3he8) with a question I couldn't answer yet: does that kind of up-front spec discipline hold on something with a real second layer, like state or a backend? Cuenta has a database, email, PDFs, and money that has to add up. This is that test.

## earlgreyhot1701D / cuenta

### Count, deliver, invoice and ledger app for a small wholesale bakery

[![Cuenta: Count. Deliver. Invoice. Ledger. A baker's paper invoice, come to life.](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fraw.githubusercontent.com%2Fearlgreyhot1701D%2Fcuenta%2FHEAD%2Fpublic%2Fog-image.png)](https://github.com/earlgreyhot1701D/cuenta/public/og-image.png)

## Cuenta

**Count, deliver, invoice, ledger for a wholesale bakery.** Built for La Condesa Baking Company in Santa Barbara.

Live at [cuentasb.vercel.app](https://cuentasb.vercel.app/). The app sits behind a PIN, so the demo video below walks through the whole thing.

## Demo video

[![Watch the 1:39 demo on YouTube](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fraw.githubusercontent.com%2Fearlgreyhot1701D%2Fcuenta%2FHEAD%2Fdocs%2Fimages%2Fdemo-thumbnail.png)](https://youtu.be/jktG-dGdQZc)

One minute and thirty-nine seconds on the production app, with mock data: Count, Deliver, the invoice, Download PDF, Send email, the Ledger and the menu.

Built from an empty folder to a working app in about 20 hours, sleep included, using the Devpost Learn skill pack.

## The problem

Eileen runs a wholesale bakery that serves four cafes. She counted what was left on each cafe's shelf on paper. She filled in her invoice forms by hand and did the math by hand. And she kept track of who owed her, and since when, in her head.

## Why Cuenta solves it

Cuenta puts the whole route in one phone-first flow: **count** …

## What it does

Cuenta takes the yellow book to the cloud. Everything is built for her phone first.

| Screen | What it does |
| --- | --- |
| Count | Pick a cafe, count what's on the shelf. Builds a history she can look back on. Planning only, it never touches an invoice. |
| Deliver | Pick a cafe, enter what she dropped off. One menu, same prices for every cafe. Totals add themselves. |
| Invoice | Her own branded invoice. Print it in the kitchen, download the PDF, or email it to the cafe. |
| Ledger | Who owes what, what's overdue, mark it paid when the money lands. |
| Customers | The four cafes and the menu. |

[![Cuenta's invoice screen: the La Condesa Baking Company invoice with the cafe's details, line items for Strawberry Tres Leches Cake, Coconut Tres Leches and Pixie Flan, an invoice total of $90.50, and Print, Download PDF and Send email buttons.](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fft6g461jkncql5gb3nhb.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fft6g461jkncql5gb3nhb.png)

The invoice had to look exactly like hers. It's her brand, the cafes know it and importantly keeping that design was absolutely essential to her.

## The skill pack interviewed me

The [Devpost Learn skill pack](https://github.com/challengepost/learn-ai-basics) is six instruction files an AI coding agent reads, from 1-start to 6-ship. I ran it in [Claude Code](https://docs.claude.com/en/docs/claude-code/overview), Anthropic's coding agent, inside VS Code.

An app with one user is exactly the kind of build where I'm tempted to skip the planning and just start. The hackathon rules didn't let me. Every entry had to come out of the skill pack, planning docs included. I'm glad they didn't.

What surprised me is who asks the questions. I usually build with [Kiro](https://kiro.dev/), where I write the spec and the agent works from it. The skill pack flips that. It interviews you, one question at a time, and writes the plan from your answers. Scope first, then the PRD (what the app does, screen by screen), then the spec (how it's built). I approved each document before the next one started.

The interview pushed back, and it caught things I would have paid for later:

- **The server clock.** Vercel, where the app runs, keeps time in UTC. An invoice made at 5:30pm in Santa Barbara would have gotten tomorrow's date and the wrong invoice number. Caught in the spec.
- **Linked prices.** If an invoice points at the current price of a flan, raising the flan from $4.00 to $4.25 rewrites every old invoice. Invoices now keep their own copy of every price, and every amount is stored in whole cents, so a total can't drift by a rounding penny. (A commenter on the Propina post, flatin.pt, pointed out the penny I'd left floating there. Cuenta counts in cents from the start.)
- **Two finish lines.** My definition of done said "E. uses it for her business." My demo plan said "mock data on camera." The agent pointed out the demo could pass while the real goal failed. We split it into hackathon done and project done.
- **Count and invoice are different jobs.** My scope draft implied the shelf count fed the invoice. It doesn't. Counting is for planning what to bake. Caught on paper. The 36 questions I wrote for E. before any of this were too many. A person running a bakery can sit through about 8 before her eyes glaze over, so I cut it to 8. Overkill is a real cost, and I'd rather plan for it than pretend it isn't there.

## Claude Code flagged its own calls

Once the plan was approved, the skill pack split the build into 8 small slices, each checked before the next one started.

Every slice report from the agent ended with a section called "Calls I made that you should check." Decisions it made that the plan didn't cover, listed for me to approve or overrule. A discard prompt it added when you switch cafes mid-delivery. A darker pink for overdue text, because the brand pink failed the contrast check. Locking the cafe account on an existing invoice, because switching wasn't free.

I’ve never had an agent hand me its own decisions like that before. Normally an agent's judgment calls stay invisible until I trip over them. Here they came to me as a list, while they were still cheap to change.

The same thing showed up when it said no. On slice 7 a permission check blocked a production deploy, so the agent couldn't run the void test the normal way. It could have edited the database directly to make the test pass. It refused, because the point of the test was to go through the real Void button, and handed it back to me.

The build had three seats. Claude Code wrote the code. A second Claude chat wrote my prompts and checked the repo between slices. I directed, tested and decided.

## Starting fresh on purpose

This was the first time I ended a long agent conversation on purpose.

I used to keep conversations going because I was afraid of losing context. Long chats get slower, cost more, and eventually compress themselves. Here, the context didn't live in the conversation. It lived in the files: scope.md, prd.md, spec.md, and a checklist with every decision written down. A fresh chat read them and picked up exactly where the last one stopped.

The skill pack says this outright: starting a fresh conversation between skills is fine, because the files carry context forward. I didn't believe it until I tried it. The docs aren't paperwork for the judges. They're the memory.

## The mistake was in the plan, not the code

On day two I did a timed run by hand, the way E. would. I found two problems. Neither one was a bug.

The first was small. Sending an email takes 5 to 8 seconds while it builds the PDF, and the button didn't change. The code already blocked a double send, but it looked frozen. Now it says "Sending…" while it works.

The second was bigger. Every cafe had its own product list. E. has one menu, and any cafe can order anything on it.

The agent traced it. The scope, the PRD and the spec all said "each cafe's standing list." The code did exactly what the plan said. Eight slices and a passing end-to-end test, all checking the plan faithfully, and the plan was wrong.

Then we traced where the plan got it. Before I ever ran the skill pack, I wrote a planning brief with Claude. That brief looked at E.'s sample invoices, saw cookies on one cafe's invoice and not the others, and guessed that each cafe had its own list. An invoice shows what a cafe ordered that day, not what it's allowed to order. I brought that guess into the scope interview as if it were already decided, so the interview never asked E.

I think that's the lesson I'm keeping. The interview checks your answers. It can't check what you bring in. Checking against the plan can't catch a mistake in the plan. Only using the thing the way the real person does could.

The comments on the Propina post saw this coming. [@mattbusel](https://dev.to/mattbusel) put it as "the thing that checks can't be the thing that built it," and suggested treating the spec as a hypothesis, not a contract. [@vladzoff](https://dev.to/vladzoff) added that the builder should never get to edit the answer key. Cuenta's end-to-end test was written from the same plan as the code, so the two agreed with each other perfectly, and both were wrong in the same way. The fix went into the spec first and the code second, with a dated line in the checklist saying why.

I had a choice. A data patch (put every product on every cafe's list) would have taken minutes. The full fix (one shared menu, drop the per-cafe table, correct the docs) took longer. I took the full fix, a week before the deadline, because E. is the user after the video, and a sixth product shouldn't have to be added four times forever.

## The 20% leaks earlier now

I told the skill pack at 1-start what I wanted to learn: my builds land at about 80% of what I imagined, and I wanted to find where the other 20% leaks.

I kept thinking of things after the fact. Again.

| Late item | Where it came from | When |
| --- | --- | --- |
| Counts separated by cafe | Me, after seeing the design mockup | before build |
| Paid by ACH, not check | E. | before build |
| Invoice numbering by cafe code and date | E. | PRD |
| Special order lines | Me | spec |
| Past counts (her paper book) | Me | build |
| 4-digit PIN not safe | Me | build |
| Getting back from an invoice on a phone | Me | build |
| One menu, not one per cafe | Me, testing by hand | after build |

Most of these lived in E.'s head, not mine. The rest showed up when I saw something concrete, like a mockup or the phone in my hand. Recognition beats recall. And on my full list of late items, seven were in the 28 interview questions I cut.

The difference this time is where they landed. Most landed on paper, or landed cheap. The interview didn't stop the 20%. It moved it earlier.

So, back to the Propina question. Does spec discipline hold once there's a database and money involved? Mostly. It held for everything that was written down as a decision. The one real miss was a guess written down as if it were a decision.

## Things that went wrong anyway

- **Real data in the mockups.** I used [Google Stitch](https://stitch.withgoogle.com/) to sketch the screens from E.'s invoice. Stitch copied her kitchen address, phone and email straight into the mockups, and the first commit included them. The agent caught it, rewrote that commit and cleared it from git history before anything was pushed. AI design tools copy your reference data into their output.
- **The PIN.** The app sits behind a PIN so E. doesn't need an account. The first version was 4 digits with no limit on guesses. I googled "is a 4-digit PIN safe?" and the answer was no. I added more digits for the PIN, with a lockout after too many wrong tries.
- **Fonts in the PDF.** The PDF is made by a headless browser on the server, and that browser has no fonts. The spec missed it. The one spike we ran before building, a timeboxed test with a pass or fail answer, found it. It passed in 10 of its 60 minutes.
- **The video was too short.** The first take of the demo was 59.9 seconds. The rules say 1 to 3 minutes. Re-took it at 1:39. We re-routed work twice. Nothing was fatal, because every slice was small and checked before the next one started.

## The numbers

| Moment | When |
| --- | --- |
| Empty folder | Sat Oct 17, about 4:30pm |
| Planning docs approved | Sat, about 6:20pm |
| First commit | Sat, 6:48pm |
| Slices 1 to 7 deployed | Sat, by 9:51pm |
| Slice 8, full test passing on the live site | Sun Oct 18, 10:45am |
| README live | Sun, 12:37pm |

About 20 hours on the clock, sleep included, and 30 commits. The full run on the live site, from counting a shelf to marking the invoice paid, takes 15.9 seconds when a test script drives it.

It runs on [Next.js](https://nextjs.org/) hosted on [Vercel](https://vercel.com/), a [Neon](https://neon.com/) Postgres database, and [Resend](https://resend.com/) for email.

## Software for one person, with money in it

Two weeks ago I wrote about [Le Voyage, a trip app I built for six people](https://dev.to/earlgreyhot1701d/a-builder-in-new-orleans-when-your-vibecoded-app-comes-on-vacation-f57). Software so specific nobody would build a company around it, and that didn't need to become a business to justify existing. I also wrote that if an app like that ever moved money, I'd be having a very different conversation with myself.

Cuenta is that conversation. It's software for one person, and it doesn't move money, but it's how she gets paid. So it got the things a trip planner never needed: a multi-digit PIN with a lockout, invoices that keep their own copy of every price, a void that never deletes, and a paid hosting plan once it runs her business.

Is it micro SaaS, the small, one-founder kind of software business? Not today. There's one user, no subscription, and nobody paying. But E. knows a lot of chefs who are one-person shows, running their businesses out of their own yellow books. Looking at what's custom in Cuenta, it's mostly data: her brand, her numbering, her menu, her cafes, her terms. The core is the same for any small wholesale food business.

So I keep wondering whether that's 20 custom builds, or one small, predictable tool that feels custom to each of them. I'd like to hear what you think.

## What it can't do

- One PIN, no user accounts. It's built for one person.
- For the first few weeks, every invoice email goes to her own inbox instead of the cafe, so she can check them before cafes get anything.
- Products and cafes can't be edited in the app yet. That comes with the handoff.
- No Excel export, no overdue aging report, no payment reminders. Stubbed for later.

## Try it

[Watch the 1:39 demo](https://youtu.be/jktG-dGdQZc). Cuenta is my entry for [Build With AI: Basics](https://learn-ai-basics.devpost.com/). The live app is behind E.'s PIN, so the video is the way in. The planning pages, the scope, PRD, spec and app map, are [published from the repo](https://earlgreyhot1701d.github.io/cuenta/), and every decision and wrong turn is in the checklist.

[![Cuenta's Ledger: stats for open invoices and amount outstanding, a list of invoices by number, cafe, date and total, one marked paid, one crossed out as void.](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fxbj9kf5evxj0qtm2f0z3.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fxbj9kf5evxj0qtm2f0z3.png)

Next is my favorite part. Her menu, her cafes, her email domain and a new PIN are already in. Now E. starts testing Cuenta on real deliveries, and I listen to her first week and decide what to add, or not.

She lost the yellow book once. Now her counts and invoices live in the cloud, not in a notebook that can go missing.

---

Quick context if you are new here. I work in the California courts, running court operations for the county. I started building with AI in July 2025 and I have been learning in public ever since. I do not write the code. I direct, the agents generate, I validate and decide. I build the [Clew Suite](https://clewlabs.org/), a set of civic tech tools for making complex systems easier to inspect.

*Built with AI assistance in October 2026. These tools move fast, so always check the source.*

AI Assisted. Human Approved. Powered by NLP.
