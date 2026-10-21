---
title: "OKF: Redefining Knowledge Bases for AI Agents"
type: "raw-source"
source_type: "article"
source_url: "https://www.analyticsvidhya.com/blog/2026/07/open-knowledge-format-okf/"
author:
  - "Shaik Hamzah"
captured_at: 2026-10-21
status: "pending"
visibility: "private"
tags:
  - "source/article"
---
# OKF: Redefining Knowledge Bases for AI Agents

## Metadata

- URL: https://www.analyticsvidhya.com/blog/2026/07/open-knowledge-format-okf/
- Author: Shaik Hamzah
- Captured: 2026-10-21T22:19:25+02:00

## Content

We use cookies essential for this site to function well. Please click to help us improve its usefulness with additional cookies. Learn about our use of cookies in our [Privacy Policy](https://www.analyticsvidhya.com/privacy-policy) & [Cookies Policy](https://www.analyticsvidhya.com/cookies-policy).

Show details

> [!note] Note
> [
> 
> India's Most Futuristic AI Conference Is Back – Bigger, Sharper, Bolder
> 
> ](https://www.analyticsvidhya.com/datahacksummit/?utm_source=blog&utm_medium=desktop_flashstrip&utm_campaign=04-May-2026&utm_content=brochure)

In June 2026, Google introduced the Open Knowledge Format (OKF), an open specification for how AI agents organise and exchange knowledge. An OKF bundle is just Markdown files, lightweight YAML metadata, and links between concepts, yet it challenges the assumption that every AI application needs embeddings and vector databases.

Because the knowledge base is plain text, it can be version-controlled in Git and navigated by following links rather than retrieving disconnected chunks. In this article, we’ll explore how OKF works and when it beats a traditional retrieval pipeline.

[Free Certification Courses](https://www.analyticsvidhya.com/courses/building-and-evaluating-rag-system/?utm_source=blog&utm_medium=free_course_banner&utm_term=free_course_auto_enrollment)

[Building and Evaluating RAG System](https://www.analyticsvidhya.com/courses/building-and-evaluating-rag-system/?utm_source=blog&utm_medium=free_course_banner&utm_term=free_course_auto_enrollment)

[

Build a RAG-based Q&A app from scratch • Diagnose pain points • Tune retrieval metrics

](https://www.analyticsvidhya.com/courses/building-and-evaluating-rag-system/?utm_source=blog&utm_medium=free_course_banner&utm_term=free_course_auto_enrollment)

## Why Traditional RAG Has Limitations

Over the past few years, **Retrieval-Augmented Generation (RAG)** has become the standard approach for providing external knowledge to Large Language Models. Instead of relying solely on the model’s training data, RAG retrieves relevant information from external documents during inference. A typical pipeline looks something like this:

![Traditional RAG Pipeline](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image3-3.webp)

Traditional RAG Pipeline

This approach works remarkably well for searching millions of documents. By comparing the semantic meaning of embeddings instead of exact keywords, RAG allows an AI system to answer questions using information that was never part of the model’s original training data.

However, there is an important trade-off. Before a document can be indexed, it must first be divided into smaller chunks. While chunking improves retrieval efficiency, it also breaks apart the original structure of the document. Relationships that were naturally connected inside a single document become distributed across multiple independent chunks.

Consider the following hospital protocol.

```
# Patient Admission Policy

Patients arriving through the Emergency Department must complete an initial triage before admission.

## Admission Requirements

- Valid patient identification
- Initial clinical assessment completed
- Emergency cases receive immediate priority

## Recording and Bed Allocation

Patient information is recorded in the Electronic Health Record (EHR) system before a bed is assigned.

Bed allocation follows the Bed Occupancy guidelines maintained by the Operations team.
```

A typical RAG pipeline may split this document into several smaller chunks before indexing.

#### 1st Chunk

```
Patients arriving through the Emergency Department must complete an initial triage.

Admission Requirements:

- Valid patient identification
- Initial clinical assessment
- Emergency cases receive immediate priority
```

#### 2nd Chunk

```
Patient information is recorded in the Electronic Health Record (EHR) system.
```

#### 3rd Chunk

```
Bed allocation follows the Bed Occupancy guidelines maintained by the Operations team.
```

Visually, the process looks like this:

![Chunking breaks the structure of the data](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image2-2.webp)

Chunking breaks the structure of the data

When a clinician asks,

***“What is the patient admission process?”***

The vector database retrieves the chunks that seem most relevant, but the logical relationships between the admission policy, emergency triage, the EHR system, and bed allocation are lost. The model has to reconstruct them on every query. This isn’t a flaw in RAG. It remains one of the best techniques for searching large, unstructured collections like PDFs, research papers, support tickets, and historical records.

Curated organisational knowledge is different. Policies, procedures, APIs, and runbooks aren’t just text, they’re interconnected concepts. Rebuilding those links from fragmented chunks on every query adds needless complexity, and that is exactly the problem OKF was designed to solve.

## What is the Open Knowledge Format (OKF)?

The ideas behind OKF did not originate with Google. Earlier in 2026, Andrej Karpathy introduced the concept of an [LLM Wiki](https://www.analyticsvidhya.com/blog/2026/04/llm-wiki-by-andrej-karpathy/): instead of repeatedly retrieving raw documents, an AI agent maintains a curated knowledge base it can continuously read, update, and improve. His analogy caught on quickly in the AI community:

Obsidian is the IDE. The LLM is the programmer. The wiki is the codebase.

The idea is simple. Humans provide source material like documentation, policies, schemas, and runbooks, and the agent organises it into a structured wiki by writing summaries, connecting related concepts, and maintaining links. Those relationships become part of the knowledge base instead of being rediscovered on every query.

Google turned this community idea into an open specification. Rather than shipping another framework or SDK, it focused on standardising the knowledge itself. The result is OKF, a lightweight format that stores knowledge as ordinary Markdown files with minimal metadata and explicit links between concepts.

An OKF bundle is just a directory of Markdown documents, each representing one concept such as a policy, API, department, runbook, database table, or metric, connected through standard Markdown links. Unlike a vector database that infers relationships through embedding similarity, OKF preserves them explicitly, so an agent follows links rather than guessing.

Because everything is plain text, it fits existing developer workflows: version-controlled in Git, reviewed via pull requests, and searchable with standard tools. Next, we’ll build a bundle from scratch to see how it is organised.

## Structure of an OKF Bundle

Now that we’ve understood the motivation behind OKF, let’s look at how an OKF bundle is actually organised. At its core, an OKF bundle is simply a directory of Markdown files. Each Markdown file represents one concept, such as a hospital policy, department, procedure, system, or operational metric. Every concept contains lightweight metadata followed by structured Markdown content. Related concepts are connected using standard Markdown links, allowing both humans and AI agents to navigate the knowledge base naturally.

The specification itself is intentionally minimal. It defines only a few conventions and avoids enforcing a rigid directory structure. This gives organisations the flexibility to organise knowledge in a way that best fits their domain while still producing bundles that can be understood by any OKF-compatible agent.

A typical OKF bundle contains the following components.

| **Component** | **Purpose** |
| --- | --- |
| index.md | Serves as the primary entry point into the knowledge base. It provides an overview of the available concepts and helps agents navigate the bundle. |
| CHANGELOG.md *(Optional)* | Records changes made to the knowledge base over time, making updates transparent and traceable. |
| Concept Files (.md) | Each Markdown file represents a single concept such as a policy, procedure, API, department, metric, or system. |
| YAML Front Matter | Stores metadata including the concept type, title, description, tags, ownership, and last updated timestamp. |
| Markdown Links | Explicitly connect related concepts, transforming the knowledge base into a navigable graph instead of isolated documents. |

## A Typical OKF Folder Structure

Although the OKF specification does not mandate a particular directory layout, following a consistent folder hierarchy makes the knowledge base significantly easier to maintain and navigate. The same organisational principles apply regardless of the domain.

The following examples demonstrate how different organisations can structure their knowledge while following the same OKF conventions.

### 1: Hospital Knowledge Base

![Hospital Knowlege Base](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image5-2.webp)

Hospital Knowlege Base

### 2: Software Engineering Knowledge Base

![Software Engineer Knowledge Base](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image4-2.webp)

Software Engineer Knowledge Base

### 3: Manufacturing Knowledge Base

![Manufacturing knowledge base](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image8.webp)

Manufacturing knowledge base

Although these examples belong to completely different industries, the underlying organisation remains remarkably similar. Every bundle begins with an index.md file that serves as the entry point, an optional `CHANGELOG.md` for tracking revisions, and a set of directories that group related concepts together.

This consistency is one of OKF’s biggest strengths. Once an AI agent understands how one OKF bundle is organised, it can navigate another bundle built using the same conventions with little or no additional adaptation.

## Building an OKF Bundle

Now that we’ve explored the overall structure of an OKF bundle, let’s build one from scratch.

For the remainder of this article, we’ll use a fictional hospital called **CityCare Hospital**. Imagine we’re building an AI assistant that helps doctors, nurses, and hospital administrators answer operational questions. The assistant should understand admission policies, emergency procedures, hospital departments, internal systems, and operational metrics. Instead of storing this information inside a vector database, we’ll organise it as an OKF bundle.

We’ll begin by creating the root directory.

![CityCare Root Directory](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image6-2-e1783329892894.webp)

CityCare Root Directory

The index.md file acts as the entry point for both humans and AI agents.

```
# CityCare Hospital Knowledge Base

## Policies

- [Patient Admission Policy](policies/patient-admission.md)
- [Discharge Policy](policies/discharge-policy.md)

## Procedures

- [Emergency Triage](procedures/emergency-triage.md)
- [Blood Transfusion](procedures/blood-transfusion.md)

## Systems

- [Electronic Health Record](systems/ehr-system.md)

## Metrics

- [Bed Occupancy](metrics/bed-occupancy.md)

## Departments

- [Emergency Department](departments/emergency.md)
```

Rather than searching the entire repository, an AI agent can first read the index to understand what concepts exist before navigating to the relevant files. This simple design keeps the bundle organised while reducing unnecessary context during retrieval.

In the next section, we’ll create individual concept files and examine how YAML metadata, Markdown content, and links work together to make the knowledge base understandable for both humans and AI agents.

## Creating an OKF Concept File

The building blocks of an OKF bundle are **concept files**. Each concept represents exactly one piece of knowledge, such as a policy, procedure, department, system, metric, or API. Keeping concepts focused makes them easier to maintain while allowing AI agents to retrieve only the information they need.

Every concept file consists of two parts:

1. **YAML Front Matter**, which stores metadata about the concept.
2. **Markdown Content**, which contains the actual knowledge along with links to related concepts.

Let’s create a concept file for the hospital’s patient admission policy.

```
---
type: policy
title: Patient Admission Policy
description: Guidelines for admitting patients into CityCare Hospital
tags:
  - admissions
  - patient-care
updated: 2026-06-15
---

# Patient Admission Policy

Patients arriving through the Emergency Department must complete an initial triage before admission.

## Admission Requirements

- Valid patient identification
- Initial clinical assessment completed
- Emergency cases receive immediate priority

## Related Concepts

- [Emergency Triage](../procedures/emergency-triage.md)
- [Electronic Health Record](../systems/ehr-system.md)
```

Notice that the file contains much more than plain text. The YAML section describes what kind of knowledge this file represents, while the Markdown body explains the concept in detail. Most importantly, the concept links to other related concepts inside the knowledge base. These links transform isolated documents into an interconnected knowledge graph that an AI agent can navigate.

## Understanding the YAML Metadata

Although OKF only requires the type field, adding additional metadata makes the bundle easier to organise and maintain.

| **Field** | **Description** |
| --- | --- |
| type | Identifies the type of concept, such as policy, procedure, system, or metric. This is the only required field in the current specification. |
| title | Human-readable title of the concept. |
| description | Summary describing the concept. |
| tags | Keywords that help organise related concepts. |
| updated | Indicates when the concept was last modified. |

Since the metadata is stored in YAML, both humans and AI agents can quickly understand what a document represents before reading its full content.

## Linking Related Concepts

One of the biggest differences between OKF and traditional document storage is that concepts are explicitly connected using Markdown links.

For example, the admission policy references the emergency triage procedure and the Electronic Health Record (EHR) system.

![Explicit Links Between Concepts](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image9-e1783329928725.webp)

Explicit Links Between Concepts

These relationships are intentionally created by the author. The agent does not have to infer them through semantic similarity because they already exist inside the knowledge base.

## Another Example: Hospital Metric

Concept files are not limited to policies. The same structure can describe operational metrics, internal systems, departments, APIs, or runbooks.

Below is a concept describing the hospital’s **Bed Occupancy Rate**.

```
---
type: metric
title: Bed Occupancy Rate
description: Percentage of inpatient beds currently occupied
tags:
  - operations
  - hospital
updated: 2026-06-15
---

# Bed Occupancy Rate

The Bed Occupancy Rate measures the percentage of inpatient beds currently occupied.

## Formula
Occupied Beds / Total Available Beds × 100

## Data Source

Hospital Information System

## Owner

Operations Department

## Related Concepts

- [Emergency Department](../departments/emergency.md)
- [Patient Admission Policy](../policies/patient-admission.md)
```

Because every concept follows a consistent structure, an AI agent can quickly understand what the metric represents, how it is calculated, where the data comes from, and which other concepts are related to it.

## How AI Agents Traverse an OKF Bundle

Once the knowledge base is organised into interconnected concept files, retrieval becomes much simpler than traditional document search.

Instead of searching thousands of document chunks, an AI agent follows a structured navigation process.

1. Read the index.md file to understand the overall knowledge base.
2. Identify the most relevant concept based on the user’s question.
3. Open that concept file.
4. Follow links to related concepts whenever additional context is needed.
5. Generate the final response using only the relevant concepts.

The traversal process can be visualised as follows.

![How a Agent Traverses OKF](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image1.webp)

How a Agent Traverses OKF

Unlike a RAG pipeline, the agent does not begin by searching an embedding index. It starts from a curated entry point and progressively explores only the concepts that are relevant to the current task.

This approach preserves the relationships between concepts while keeping the amount of context sent to the language model relatively small.

## Why This Works Well for AI Agents

The biggest advantage of OKF is that it allows developers to organise knowledge in the same way humans naturally think about it. A doctor reading the hospital’s documentation does not randomly jump between unrelated paragraphs. They begin with a policy, follow references to procedures, consult the relevant systems, and then arrive at the information they need. OKF enables AI agents to follow this same workflow.

Instead of reconstructing relationships from fragmented document chunks every time a question is asked, the agent navigates an explicit knowledge graph where those relationships have already been defined. This makes the retrieval process more deterministic, easier to audit, and significantly simpler to maintain.

## Where RAG Still Excels

At this point, OKF sounds like an ideal solution for organising knowledge. It preserves relationships between concepts, keeps everything version-controlled, and allows AI agents to navigate curated documentation without relying on semantic search.

However, OKF has an important limitation. Someone has to curate every concept.

Every policy, procedure, system, metric, and department must be written, reviewed, and maintained. This works well for authoritative organisational knowledge, but it becomes impractical when the knowledge base grows to millions of documents.

Consider a hospital that has accumulated years of operational data.

- Millions of Electronic Health Record (EHR) entries
- Medical research papers
- Clinical notes
- Patient feedback
- Incident reports
- Internal emails
- Meeting transcripts
- Equipment maintenance logs

Organising every one of these documents into carefully curated OKF concept files would require an enormous amount of manual effort. Even if AI agents assisted with the curation process, much of this information changes continuously and is better suited for semantic search.

This is where **Retrieval-Augmented Generation (RAG)** continues to be the preferred solution.

### RAG Solution

Rather than requiring documents to be manually organised, RAG indexes large collections of unstructured data using embeddings. When a question is asked, the system retrieves the most semantically relevant documents and provides them as context to the language model.

For example, consider the following questions:

- *Has anyone encountered this MRI scanner error before?*
- *Find previous incident reports involving delayed laboratory results.*
- *Summarise discussions about the new EHR rollout.*
- *Search for all meeting notes mentioning patient transfer delays.*

These questions cannot be answered from a small curated knowledge base. Instead, they require searching through thousands or even millions of documents where the answer could exist anywhere. This is exactly the type of problem RAG was designed to solve.

The strengths of each approach become much clearer when viewed side by side.

| **Feature** | **OKF** | **RAG** |
| --- | --- | --- |
| Best for | Curated organisational knowledge | Large collections of unstructured documents |
| Knowledge Source | Markdown concept files | Raw documents |
| Retrieval | Deterministic navigation | Semantic similarity search |
| Infrastructure | File system + Git | Embeddings + Vector Database |
| Version Control | Native Git support | Requires re-indexing after updates |
| Relationships | Explicit links between concepts | Inferred from retrieved chunks |
| Scalability | Moderate | Excellent |
| Explainability | High | Moderate |

Neither approach is universally better than the other. They simply solve different problems. OKF provides structure and precision. RAG provides scale and flexibility. This naturally raises another question.

**Do we really have to choose one over the other?**

*Fortunately*, the answer is **no**.

## Hybrid Knowledge Architecture: Combining OKF and RAG

In practice, the most effective AI systems use both OKF and RAG together.

Instead of treating them as competing technologies, modern agent architectures use each one where it performs best.

A simple way to think about this is the **80/20 principle**.

- The **20%** of organisational knowledge that is critical, stable, and frequently referenced is stored as an OKF bundle.
- The remaining **80%** of large, unstructured information stays inside a traditional RAG pipeline.

This creates a layered knowledge architecture.

![Hybrid Knowledge Architecture](https://cdn.analyticsvidhya.com/wp-content/uploads/2026/07/image7-1.webp)

Hybrid Knowledge Architecture

The router determines which knowledge source is most appropriate for the incoming query.

Questions requiring authoritative and deterministic answers are routed to the OKF bundle.

#### Examples include:

- What is the patient admission policy?
- How is the Bed Occupancy Rate calculated?
- Which system stores patient medical records?
- What is the emergency blood transfusion procedure?

Each of these questions has a single authoritative answer maintained by the organisation.

On the other hand, exploratory questions are routed to the RAG pipeline.

#### For example:

- Has anyone encountered this MRI scanner error before?
- Find previous incident reports involving delayed laboratory results.
- Summarise discussions about the EHR migration project.
- Search meeting notes discussing patient discharge delays.

These questions require searching large collections of historical documents rather than consulting curated knowledge.

This hybrid architecture allows each system to focus on its strengths.

| **OKF Strengths** | **RAG Strengths** |
| --- | --- |
| Deterministic retrieval | Semantic retrieval |
| Curated and authoritative knowledge | Massive document collections |
| Explicit relationships between concepts | Finds information using semantic similarity |
| Version-controlled with Git | Continuously indexes new documents |
| Easy to audit and maintain | Highly scalable |

Perhaps the biggest advantage of this architecture is that the language model does not need to know where the information comes from. The agent simply requests the knowledge it needs.

The routing layer decides whether that knowledge should come from the OKF bundle or the vector database. Frameworks such as [LangGraph](https://www.analyticsvidhya.com/blog/2024/07/langgraph-revolutionizing-ai-agent/), [LangChain](https://www.analyticsvidhya.com/blog/2024/06/langchain-guide/), or LlamaIndex make this routing straightforward by allowing developers to build workflows that choose the appropriate retrieval strategy based on the user’s query. As a result, AI agents gain the precision of curated knowledge without sacrificing the ability to search vast collections of unstructured information.

In other words, the future is not OKF versus RAG. It is OKF plus RAG, working together as complementary layers in a single knowledge architecture.

## Conclusion

The Open Knowledge Format offers a simple, transparent way to organise knowledge for AI agents. By representing it as interconnected Markdown documents, OKF keeps organisational knowledge easy to understand, maintain, and version-control in Git.

It suits curated information like policies, runbooks, and API docs, without replacing RAG, which still excels at semantic search across large, unstructured collections.

Used together, the two cover far more ground than either alone. Ultimately, knowing where each approach fits is what lets developers build agents that are accurate, explainable, and production-ready.

### Frequently Asked Questions

## Q1. What is the Open Knowledge Format (OKF)?

A. It is an open specification Google introduced in June 2026 for how AI agents organise and exchange knowledge. An OKF bundle is a directory of Markdown files with lightweight YAML metadata and explicit links between concepts, so knowledge lives as plain text alongside your code rather than as vectors in a database.

## Q2. How is OKF different from RAG?

A. RAG splits documents into chunks, embeds them, and retrieves the most semantically similar pieces at query time. OKF stores knowledge as interconnected concept files and lets an agent navigate by following author-defined links. RAG infers relationships; OKF keeps them explicit.

## Q3. Does OKF replace RAG?

A. No. They solve different problems. OKF is best for curated, authoritative knowledge like policies, runbooks, and API docs. RAG is best for searching large, unstructured collections such as EHR entries, incident reports, and meeting notes. The article recommends using them together.

## [Become an Author](https://www.analyticsvidhya.com/become-an-author)

Share insights, grow your voice, and inspire the data community.

[
- Reach a Global Audience
- Share Your Expertise with the World
- Build Your Brand & Audience
](https://www.analyticsvidhya.com/become-an-author)

[![imag](https://www.analyticsvidhya.com/wp-content/themes/analytics-vidhya/images/Write-for-us.webp)](https://www.analyticsvidhya.com/become-an-author)

[![Popup Banner](https://imgcdn.analyticsvidhya.com/freecourses_cms/Banner-DHS-26.jpg)](https://www.analyticsvidhya.com/datahacksummit/?utm_source=web_property&utm_medium=desktop_popup&utm_campaign=06-May-2026%7C%7CDHS&utm_content=explore)

[![AI Popup Banner](https://imgcdn.analyticsvidhya.com/freecourses_cms/Banner-DHS-26.jpg)](https://www.analyticsvidhya.com/datahacksummit/?utm_source=web_property&utm_medium=desktop_popup&utm_campaign=06-May-2026%7C%7CDHS&utm_content=explore)
