---
raw_path: raw/articles/Google's OKF - The New Way to Structure Your Knowledge for
  Agents.md
content_hash: 548dad20315c390445427ab2f32c1b770739e7215ec4f1753fde9bd756d5f1d2
title: Google's OKF - The New Way to Structure Your Knowledge for Agents
---

# Google's OKF - The New Way to Structure Your Knowledge for Agents

## Metadata

- URL: https://www.youtube.com/watch?v=MY9F9K7wWX4
- Author: Marie Haynes
- Captured: 2026-10-21T22:43:42+02:00

## Content

Google just announced the Open Knowledge Format (OKF), a new way to structure your knowledge for AI agents. This standard uses simple Markdown to make business and personal insights accessible to the agentic web. In this video, I break down why this changes SEO, how to build your first OKF bundle, and the potential for selling expert knowledge directly to AI systems.  
  
Google's blog post on okf:  
https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/  
  
The Spec.md file for OKF on Github:  
https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md  
  
Andrej Karpathy's LLM-Wiki:  
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f  
  
Join me in my community at the Search Bar:  
https://community.mariehaynes.com  
https://mariehaynes.com/join - for more on the paid areas.  
  
0:00 - Introduction to Google's Open Knowledge Format (OKF)  
  
1:03 - How OKF changes SEO and makes businesses accessible to AI agents  
  
1:43 - Selling proprietary knowledge and OKF bundles  
  
2:21 - How to use NotebookLM and Gemini to learn the new standard  
  
3:02 - What is OKF? (Markdown files and the LLM Wiki pattern)  
  
4:01 - Breaking down the OKF spec (Human and agent-friendly format)  
  
5:03 - Terminology: Creating "Knowledge Bundles" and directories  
  
5:51 - Structuring concepts as single Markdown files  
  
6:30 - Understanding YAML front matter (Type, title, descriptions, tags)  
  
7:18 - Formatting the body, citations, and cross-linking  
  
7:40 - Organizing files: Index files, log files, and using Git/Obsidian  
  
9:11 - Practical examples: BigQuery data vs. triggered Playbooks  
  
11:12 - Andre Karpathy’s LLM Wiki pattern explained  
  
13:48 - Letting the LLM write and maintain your knowledge wiki  
  
14:34 - Why OKF is the "new schema" and future revenue streams  
  
17:15 - How agents discover your OKF (llms.txt) and "Semantic Unbaking"

## Transcript

### Introduction to Google's Open Knowledge Format (OKF)

**0:00** · Google just announced something called the Open Knowledge Format, and boy am I excited about this. This is a whole new layer for the internet. It's a way to take your knowledge, your business knowledge, your personal knowledge, whatever it is, and structure it so that agents can understand it. Now, this is nothing new. The way that they do it is they structure it in markdown files.

**0:20** · It's actually very, very simple. We'll look at some examples in just a minute.

**0:24** · But, what is new is that it is a standardized way of doing this. So that if my agent wants to access your public OKF, then it can happen standardized. I don't need to use any particular software to do it.

**0:41** · I could use something like Notion or Obsidian to look at the markdown files.

**0:45** · I could ask my agent to make a web page out of it. I could do all sorts of things, but the key thing is that I have access to the knowledge that a business has chosen to provide. This is a really big deal. I think it's going to change how we do SEO. I think we're going to need a different acronym. It's not SEO, it's not GEO, it's not even agentic search optimization. This isn't about getting found, rather it is a way to make your business accessible to agents.

### How OKF changes SEO and makes businesses accessible to AI agents

**1:15** · Not just accessible, but make it so that agents can do things with your business knowledge. I do think that people who understand OKF will be in high demand. I think it's going to be a new service that SEOs offer where kind of like making a site map, but much more detailed, where people will be really good at understanding how to take a business's knowledge and turn it into a knowledge graph that is an OKF.

**1:38** · But, I think it's even more exciting for people who actually have proprietary knowledge, processes, or something that people already pay you for, because you will be able to, I'm fairly certain, I'm not I don't know this 100% for sure, but you should be able to sell your OKF bundles and that way you can have access to an expert's knowledge and even integrate it into your own OKF.

### Selling proprietary knowledge and OKF bundles

**2:05** · So that you will have, you know, we'll probably buy OKF bundles from a lawyer, from an accountant, from an SEO. And I I think this is a very very exciting thing. So this is a proposed standard. It is just the very first version and so if you're watching this in the future, I'm recording this mid-June. There probably are some new versions that are out there. I'd encourage you to do what I did is take I've put some links in the description for Google's documentation on this and also the spec file in GitHub.

### How to use NotebookLM and Gemini to learn the new standard

**2:38** · Put all of that into a Notebook LM. Give that notebook to Gemini and then ask Gemini to summarize the information and tell you how you can use this in your business. One good prompt would say would be to say, "Give me 20 ideas of how I could use OKF in my business." So let's get into Google's description of what OKF is. OKF is a specification that formalizes something called the LLM Wiki pattern. This pattern was described by Andre Karpathy.

### What is OKF? (Markdown files and the LLM Wiki pattern)

**3:08** · We're going to look at that in just a minute. But first let's look at what an OKF is. It is just Markdown. If you're not familiar with Markdown, it's just a really simple way to describe text, you know, as text. Uh basically a text file that might have a little bit of markup to say this is a heading, this is bolded, or whatever.

**3:28** · Just a very simple way to understand text. It is really easy for agents to understand text. Now, we're not going to be taking every page of our website and turning that into a Markdown file. I mean, we could. We're actually going to take the things that we have on our website, extract the concepts from those, and make those concepts their own Markdown files. Let's see if if can explain that a little more clearly. I found that this was the most helpful document that Google produced. It's on GitHub. Again, it's linked to in the description, the spec.md file.

**3:57** · I'm actually going to read a part of this because it explained things really well.

### Breaking down the OKF spec (Human and agent-friendly format)

**4:04** · OKF is an open human and agent-friendly format, so it's not just for agents, humans can use it as well, for representing knowledge, the metadata, the context, and the curated insight that surrounds data and systems. It's designed to be authored by people, generated by agents, exchanged across organizations, which I think is the really exciting thing, and consumed by both.

**4:29** · They say that the format is intentionally minimal, and what they mean by this they're going to say some words that if you're not into markdown, cuz I I didn't know what a YAML front matter is, but we're going to discover that. It's actually very, very simple. There's no schema registry. When I first saw this, my thought was this is just schema. The thing is that it's so simple that you don't need to specifically outline every specific thing that this is an entity, that this is you'll see what I'm talking about.

**4:59** · I think it's important to look at the terminology that Google gives us. We are going to be creating what's called a knowledge bundle. This is a collection of files. So, OKF is essentially a directory of directories, and in those directories are a bunch of markdown files. Nothing new, but again, the fact that it's standardized is the important thing here. I'm fairly certain that these OKF bundles are things that you could buy or sell.

### Terminology: Creating "Knowledge Bundles" and directories

**5:24** · So, again, like if I have I have my page on Google algorithm updates and things that changed with AI that might be relevant to rankings, I might sell that as a knowledge bundle that you can purchase, and then instead of having to access an MCP for my uh my website or to use Web MCP, you would essentially integrate my knowledge into your system. Each of the markdown files in these directories represents a concept.

### Structuring concepts as single Markdown files

**5:56** · And this is the the concept, no pun intended, that's hard to understand here because we're used to as SEOs uh taking a webpage and saying, "All right, here is the summary of the webpage." Instead, each markdown file is a concept, a single unit of knowledge within a bundle represented as one markdown document. So, one website might produce maybe 50 or maybe 10 or maybe even more concepts that each would be their own markdown file. Let's talk about what this YAML front matter is.

### Understanding YAML front matter (Type, title, descriptions, tags)

**6:30** · This is the information that is required in these markdown files. And then after this information, you can put whatever you want in the file. So, the you're going to have the the type, the title, the description of here's what's in this file, uh resource, tags. The tags can be different topics that are covered and uh and then a timestamp. All of this will be really easy. Your agent will do it for you. It's not something that you need to really pay a lot of attention to.

**7:00** · What you're probably going to do is give this spec.md file to your language model and say, "Create the YAML front matter for me." Then, after that, are the instructions or the knowledge or the data tables or whatever it is that you want to share on that particular topic.

### Formatting the body, citations, and cross-linking

**7:18** · After the front matter, then there is the body that has everything else in it.

**7:23** · And there can also be links. And this is where it's really interesting because eventually what you're creating is a knowledge graph of all of your knowledge, which is really, really interesting. You can also have citations that help support a claim in the body.

**7:37** · You don't necessarily have to have that.

**7:39** · Here's an example of how the bundle can be structured or how it's supposed to be structured. The index file is where the every one of these has to have an index file. This is really interesting, the log file. A log file can be so that your agent says, "Oh, I updated this today. I did this today." And we'll look at Karpathy's wiki in a minute because it's really interesting how the role that your agents play in this. The concept is the most important thing here. Again, my concept might be web MCP.

### Organizing files: Index files, log files, and using Git/Obsidian

**8:08** · And then I will have a sub I could have subdirectories. Maybe my concept is MCP and I have subdirectories for web MCP and for other things. This is what's going to take some time is for us to figure out how to structure these because every business is going to be different. Then you can store all these files in a Git repository. If you don't know what that is, it's essentially just uploading it to GitHub, totally free to do that. You can also store it in a markdown organizer like Notion or like Obsidian.

**8:38** · Um when this first came out, I thought that it would be a replacement for Obsidian. I haven't used Obsidian, but here's why I said that because I was considering getting something like Obsidian. And now I'm like, "Oh, actually I can just create my own markdown files. I could create my own front end to look at those markdown files. I don't think I'm going to need a way to store and to organize all the markdown files." But who knows, I could be wrong on that. Now, many of the examples that Google gives us are not quite what I'm talking about.

### Practical examples: BigQuery data vs. triggered Playbooks

**9:11** · So, they talk about using the OKF as a way to get big query data, especially from GA4, which I think is really, really interesting. And it is something that I want to do. I don't think it's actually where the power is for most of us who are are watching this video. And this example that they give is is it takes a while, at least it took me a while to wrap my head around it. So, we have the stuff that needs to happen, that needs to be there at the top, which we just talked about.

**9:39** · And then this is the body, which you don't need to have schema in your body. You don't need to have joints. You don't need to have citations. These are things that this business, this organization is saying, "When we look at customer orders, this is how we organize them." If you didn't have this, if you were just using rag, if you were just using a language model to say, "Get me the information from BigQuery and organize it," it would guess in how you are going to organize things. This way you can say, "This is how we do it.

**10:11** · This is our way of organizing things." Here's another example, and I think this is one that I'm going to use a lot. The type is a playbook, which is kind of like the process. And this playbook would be triggered when a particular thing happens. So mine might be in my overall OKR of my knowledge, might be a trigger that happens uh when somebody talks about a traffic drop. And then I would say I have a playbook for diagnosing why your traffic has dropped. Uh that's the type of thing.

**10:42** · So basically I'm saying to your agent, "Here's where you go in my brain to get this information." And then the interesting thing is the cross-linking. And this is something where I think it's going to be very exciting, where we can start to see the connections between things that we've talked about. I'm going to we'll we'll know more about this. This will be more interesting when we look at Karpathy's wiki, because I think this is uh really, really important to pay attention to. So let's actually look at Andrej Karpathy's LLM wiki.

**11:09** · This is not exactly what the OKR is, but I found that reading this helped me understand the power of what we can do with these OKRs a lot better.

### Andre Karpathy’s LLM Wiki pattern explained

**11:20** · Karpathy says that uh he talks about the idea that most people with when we're using LLMs and you're using documents, you're thinking of rag, that you're giving your LLM this massive amount of context and saying, here's a question, go find the parts that are relevant in all of this context in the entirety of your website, and you're relying on your agent to do a lot of work.

**11:42** · Whereas, his LLM Wiki is basically saying, like, here are Here's a Here's a map to where the important things are in our in our knowledge. But, here's the part that I'm really excited about. In his model, instead of just retrieving from raw documents at query time, the language model incrementally builds and maintains a persistent Wiki. And so, he talks about when you add a source, it's not like you're adding a page to a site map in your website.

**12:13** · Instead, your language model, I think we're all going to have to create There probably will be tools that do this for us, but I think the best ones will be ones that we create ourselves. We will When you add a source, the language model doesn't just index it for later retrieval. It reads it, extracts the key information, and integrates it into the existing Wiki, updating entity pages, revising topic summaries, noting where new data contradicts old claims, strengthening or challenging the evolving synthesis.

**12:42** · So, let's say that today this video goes into my OKF. The topics that I talk about get extracted, and each of them get their own markdown file. Now, let's say that a couple months from now, I do another thing about OKF. Maybe I give an example of how I used it. I did actually create an OKF of our peppers in our garden. I'll share that at some point.

**13:08** · So, let's say I share that, then it's not like that's going to create a whole new set of concepts. The concept of OKF has already been discussed, and so what my language model should do is say, "Oh, we already have discussed the idea of OKF. Let's see where I can add to the body in that information, and then it might also discover new links that maybe I have said that OKF is connected to revenue that you can can gain from building this type of thing.

**13:40** · Again, more on that in just a minute. In Karpathy's version, he says you never or rarely write the wiki yourself. And this is the part that's hard to wrap my head around that the language model is going to write and maintain all of it. So, once you get it going, your job is to find new information. Your job is to learn things and to maybe write about them, to share them. It doesn't even have to be your knowledge.

### Letting the LLM write and maintain your knowledge wiki

**14:04** · Perhaps when Google publishes new documentation, I put that into my OKF and that becomes, you know, the concepts are Google documentation and and things like that. He talks about a few ex- here and I I honestly I think that it's endless what we could use this for. I think that anytime you want to take a bunch of knowledge and you want to do stuff with agents, this is what we're going to use. So, let's talk about where this is going because I think that this is the new schema.

**14:32** · I think it's funny because I have historically really struggled with understanding I understand the importance of some schema. If you have an e-commerce site and you have rapidly changing product prices and things, schema helps the the web helps Google, helps agents understand rapidly changing things on your website. But I didn't like the idea of mapping out every individual entity on your site, every piece of schema. I just didn't understand that.

### Why OKF is the "new schema" and future revenue streams

**15:01** · And the reason is that the web is not our knowledge is not like that. It's not natural. This what Google has described here is a natural way to say, here's what I learned, now go categorize it into my brain. And I think that this is going going evolve over time. Again, this is just a very early first version.

**15:24** · I do think that we will have two revenue streams here for most of you who are watching this video. One is selling this service to businesses. There will be tools. I know Saganth Mahanadossan has created already a tool that will take your web pages and turn them into an OKF bundle. However, he is, I think, just taking each web page. He's not actually doing the concepts. I'm sure that that will come.

**15:50** · I'm sure there will be many tools, but I think that there will be great skill in knowing individually and understanding a business and understanding how to organize that knowledge that is going to be very, very valuable. So, I would encourage you to play with this, to create an OKF of just something. It doesn't have to be your entire website, but just something so that you can use it. The next thing is that this will be valuable to people who have knowledge to sell.

**16:17** · And I you think that we're going to sell OKF bundles to each other. I think that kind of blows my mind at how all of a sudden, I won't just have an MCP where I can get legal information to review a document. Like, I could have my lawyer or the best lawyer in this area, you know, have his or her OKF and and have that as part of my business intelligence. It is really hard to to wrap my head around that.

**16:45** · And I think and then not only that, it's not like I'm just having their files and their static knowledge, but as the law changes, then what I need to know for my business knowledge gets updated as well.

**16:59** · But we're going to build this whole entire network of a brain where those who have knowledge and expertise in an area will be very, very valued. Another question that I saw come up is how will agents know that you have this OKF? And I actually think it's going to be in your LLMs.txt that there will be a direction to agents to say that you have an OKF bundle.

### How agents discover your OKF (llms.txt) and "Semantic Unbaking"

**17:23** · We'll see what happens with that. I'm going to end with this phrase that Gemini gave me. I've spent endless hours brainstorming on what OKF means, and Gemini gave me the phrase semantic unbaking. And I think that that's just amazing. I think that we're going to be able to take our knowledge and instead of having to work like machines and make it into something that is machine readable, we're actually just going to be able to have these lives where we learn stuff and we share stuff, and those who work hard to develop expertise

**17:54** · will be able to be rewarded and we'll be able to help a lot of people with this.

**17:58** · I hope you found this interesting. I will be writing more about OKF in my community, community.maryhines.com, and uh thanks so much for watching. I wish you the best of luck with everything.
