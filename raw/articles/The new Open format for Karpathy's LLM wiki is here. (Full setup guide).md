---
title: "The new Open format for Karpathy's LLM wiki is here. (Full setup guide)"
type: "raw-source"
source_type: "article"
source_url: "https://www.youtube.com/watch?v=iod1M9Dc3HI"
author:
  - "Agent Glitch"
captured_at: 2026-10-21
status: "pending"
visibility: "private"
tags:
  - "source/article"
---
# The new Open format for Karpathy's LLM wiki is here. (Full setup guide)

## Metadata

- URL: https://www.youtube.com/watch?v=iod1M9Dc3HI
- Author: Agent Glitch
- Captured: 2026-10-21T22:43:13+02:00

## Content

![](https://www.youtube.com/watch?v=iod1M9Dc3HI)

Your AI second brain has a problem: your agent can open anyone's LLM wiki, but it can't find anything in it - because there's been no standard for how these wikis are built. Google's new Open Knowledge Format fixes that with just markdown, folders, and one required field, and in this video I show you how it works and how to adopt it with literally one prompt.  
  
Karpathy's LLM wiki- https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f  
Google's OKF blog - https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing  
  
Google's OKF github - https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf  
  
Google's OKF spec.md file - https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md  
  
  
#ai

## Transcript

### The evolution of wikis

**0:00** · So, around 3 months ago, Andre Karpathy dropped a single .md file on GitHub that literally changed how thousands of people build their own second brain. So, the way to use this is very simple. You just copy the URL and paste it inside your Claude code or Codex session and direct it to a particular directory. And then it will create a knowledge base for you out of that. So, as you can see over here, this is my own second brain, which has all of the pages as well as the index log available.

**0:26** · Now, I can go ahead and see the graph view of the same and see how every page is connected to each other. So, what is the problem with this approach? Why LLM Wiki 2.0 came in? The problem with this approach is that everybody who built their own knowledge base using this, including me, ended up with their own structure completely different from everybody else. And sure, your agent can open my Wiki because it's just a markdown file, but it cannot find anything inside it. It does not know my folders, my index, my metadata.

### The portability problem

**0:56** · It has to reverse engineer my whole system before it can answer a single question for you. And half the time it won't even try to answer the question. And when it does, the answer will probably be wrong.

**1:09** · So, what's the solution to this? So, a couple of weeks ago, Google published their open spec, which exactly fixes this problem. It's called the open knowledge format, and I'm going to show you how to adopt this to your own particular Wiki. Or if you're starting from scratch, how to adopt this particular format so that your second brain is shareable. Okay, so here's the plan. First, we'll do a quick recap of the LLM Wiki pattern in case you missed it. Then the actual problem OKF is solving. Then we go through the spec itself. It's actually very short, and honestly, that's the best thing about it.

### Introducing OKF

**1:41** · I'll show you how to convert your existing knowledge base with a single prompt. We look at what Google shipped alongside the spec. And at the end, I'll get into the biggest criticism I've seen, that is OKF is actually too simple to matter. So, let's get into it. The core idea goes like this. So, most of us, when we want an AI to know our stuff, we do rag. We dump documents into a vector database, we index everything, and at query time, the model retrieves some chunks and pieces an answer together. It works, but nothing accumulates. Every single answer starts from scratch. The LLM Wiki flips it.

### Core wiki concepts

**2:14** · So, instead of indexing raw documents, your agent reads each new source, meeting notes, articles, plans, whatever you feed it, and pulls out the key information, and merges it into a persistent wiki. That is structured markdown files, which are linked to each other with entity pages for the people, the tools, and the concepts that actually keep showing up. And the wild part is that how little effort it takes on your end. And the best part is how easy it is to use.

**2:41** · So, for example, if I want to add a new knowledge source to my particular wiki, what I'll do is just paste the URL and say, "Add this to my wiki." Now, it will read the URL and create an actual page of what particular article this is, which is around how LLM works. And that's it. Now, my wiki will have a node which tells it how LLM works, and it will automatically connect it to other pages which have similar concepts. Now, let's move on to the problem. What's the problem in this?

### Structural fragmentation

**3:10** · It's working perfectly fine. Why do you want to include 2.0? The problem is this gist file itself. It actually says that the agent will build out the wiki with you. That means you will customize it and personalize it, but that actually also means that other people cannot use it. They will personalize it in their own ways. So, let's take an example. My agent might file things under a concepts folder with a tags field. Yours might use topics folder with a categories field. The thing is, it's the same idea, but totally different structure. And that means these wikis don't travel.

**3:41** · So, suppose say I have spent 6 months building a knowledge base about my whole stack, and I hand it to a teammate.

**3:50** · Their agent have two options, and both are bad.

**3:53** · So, option one is read the entire thing whenever a new question comes up. That works right up until the vault outgrows the context window. And then you're burning the same amount of tokens that you wanted to save in the first place by moving on with the structure. Option two is reverse engineer my conventions before doing any real work. And here's the nasty part. It might not bother. It won't even throw an error. It will quietly skip the categorical search it does not know exist. It will answer from two files it happened to open and you'll never know it missed the third file or it missed anything else.

**4:24** · Little mismatches like my tags versus your categories compound exactly like that and it will be one silent failure at a time. So, just wait for a moment and think about what you could do with a really good knowledge base source. You can share it with your teammate and they can enrich it by adding more and more new sources. And these new sources can be referred by all of the agents that are using it. You can publish a knowledge base for your own community from one tool to another without worrying about redoing everything.

### Benefits of standardization

**4:52** · Every one of those use cases need to agree on a format. And up until two weeks ago, there was no such format. So, how do you actually use this? And this is the part I love the most because it's so simple.

### Implementing the OKF spec

**5:04** · Think of this spec file as a normal skill file and the structure is also the same. So, you'll have your terminologies, your bundle structure, your concept documents where it will have the front matter, the body and some examples for the agent to understand it better. You will have your cross linking and then towards the end the index files and the log files which are optional. So, what do you do?

**5:29** · You just copy this raw file and paste it inside any of your agent like Lord code or code X if you're starting from scratch and you just add a prompt that says that build a knowledge base for me using this particular spec.md file and it will do it for you. Now, what if you are actually not starting from scratch and you already have a knowledge-based present, and you want to refactor that particular knowledge base to follow this particular format. In that case also, you will do do the same thing.

**5:54** · I'll just copy my raw file and go to my cloud session where I have my knowledge base connected to this, and I'll just say that refactor my knowledge base using this spec.md file. And that's it. It will go on read my entire directory, my knowledge base, and make sure each and every page is following this new format.

**6:17** · Once it's done, I'll let you know how it looks like, and we'll try it out. And once your knowledge base has been refactored, let's test how does it differ if I go by the old approach versus the new approach. On the left-hand side, you see is the original Carpati style LLM Wiki, wherein I have asked a query which resides in my knowledge base. And as you can see, it is beautifully simple. There is one Wiki file and one pages folder, and the model can quickly read through it. And it works well for a personal Wiki.

### Performance and conclusion

**6:44** · But the problem starts when the Wiki starts to grow, and everything becomes dependent on how I personally named and organized things. So, for example, this thing will stop making sense if I share it with somebody else. On the other hand, you see the new Wiki, how does it work? You can see the information is split into much more clearer sections like creative, YouTube, experiments, and profile. And this is much more scalable.

**7:12** · It is not just my private note-taking style anymore, and it becomes a standard structure that any other person can use or any other AI agent can understand.

**7:21** · And the trade-off is that you might require some more searches initially, as you can see being done over here. But once you add good indexes and summary, it becomes much better for long-term retrieval. So, the way I think about is that the old Wiki is great for a small personal memory, and the new Wiki is better as a shared knowledge system. It scales, it can be standardized, and it can be used across people, projects, and agents. So, that was it. Links to all of the repos, as well as blog article referred in this video, will be attached in the description below.

**7:52** · Make sure to like this video and subscribe to my channel for more such awesome AI content.
