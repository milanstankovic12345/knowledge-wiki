---
raw_path: raw/articles/Building RAG Systems From Zero to Hero.md
content_hash: a8fc1cb7328c160be35830d0596b84d65a3fbe019e37551a6721b4cbc142c1c9
title: 'Building RAG Systems: From Zero to Hero'
---

# Building RAG Systems: From Zero to Hero

## Metadata

- URL: https://dev.to/gautamvhavle/building-production-rag-systems-from-zero-to-hero-2f1i
- Author: Gautam Vhavle
- Captured: 2026-10-20T10:26:53+02:00

## Content

*What I learned building RAG systems from scratch—and how you can too*

---

## The Journey That Changed How I Think About AI

Recently, I finished a comprehensive RAG [course](https://www.coursera.org/learn/retrieval-augmented-generation-rag) from DeepLearning.AI and instructor was Zain Hasan. Before that, I'd been learning from scattered tutorials and blog posts—completely unstructured. I thought I understood retrieval-augmented generation. I knew the theory: embeddings, vector databases, semantic search.

But like most things in engineering, theory and practice are worlds apart.

Since then, I've been building RAG systems for standalone projects personal/course, a customer support chatbot, a documentation search engine, and an internal knowledge assistant. Each one taught me something which just reading theory couldn't: the messy, fascinating reality of production AI.

Here's what I wish someone had told me before I started, and what I've learned along the way.

---

## Why RAG? The Problem I Kept Running Into

During my course, the instructor kept hammering home one point: LLMs are amazing at reasoning, terrible at remembering. I nodded along, but I didn't *really* get it until my first project.

I was building a chatbot for a company's internal documentation. Simple, right? Feed GPT-4 a question, get an answer. Except:

1. **It hallucinated constantly.** Made up API endpoints that didn't exist. Confidently cited documentation sections that were never written.
2. **It didn't know about latest updates.** We could have shipped a major feature last week. The model? Clueless.

That's when RAG clicked. Instead of expecting the model to memorize everything, I'd give it a search engine. When someone asks a question, search the docs first, then feed the relevant content to the model.

Suddenly: no hallucinations, always up-to-date, and token utilization also was optimized.

**That's the power of RAG.**

---

## What is RAG? How I Explain It Now

After building a few systems, here's how I think about RAG:

Instead of asking an LLM to answer from memory (which leads to hallucinations), you:

1. **Store your documents** in a database that understands meaning (vector database)
2. **When someone asks a question**, search for relevant documents
3. **Hand those documents to the LLM** along with the question
4. **Let the LLM answer** based on what it just read

It's like the difference between asking someone to recite a textbook from memory versus letting them look it up first.

**The breakthrough:** You separate "knowing facts" from "reasoning about facts." Update your documents, and your AI instantly knows the new information. No retraining needed, no stale knowledge, no made-up answers.

---

## Foundation: Understanding the Building Blocks

Before we build, let's ensure we're on the same page about three key concepts:

### 1\. Embeddings: GPS Coordinates for Meaning

Embeddings convert text into arrays of numbers (vectors) that capture semantic meaning. Words with similar meanings sit close together in this mathematical space.

```
"dog" → [0.32, 0.89, -0.45, ...]
"puppy" → [0.34, 0.87, -0.43, ...]
"car" → [-0.12, 0.15, 0.78, ...]
```

**Key Insight:** Embeddings let us compute "semantic similarity" mathematically. "Dog" and "puppy" are geometrically close; "dog" and "car" are far apart.

[![Image about RAG](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fxh7xaq9i4k7prtyv05e6.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fxh7xaq9i4k7prtyv05e6.png)

### 2\. Vector Similarity: Finding the Needle

When a user asks "What's your refund policy?", we:

1. Convert the question into an embedding
2. Find documents with similar embeddings (using cosine similarity or dot product)
3. Return the top matches

This is wildly faster than reading every document. A vector database can search millions of documents in milliseconds.

### 3\. Context Windows: The LLM's Short-Term Memory

LLMs have limited context windows (think RAM for conversation):

- GPT-3.5: 4K tokens (~3,000 words)
- GPT-4: 8K-128K tokens
- Claude 3: Up to 200K tokens

**The catch:** More context = slower response + higher cost. RAG is about finding the *right* context, not *all* context.

---

## The RAG Pipeline: End-to-End Architecture

Here's how a production RAG system works:

### Phase 1: Ingestion (Building Your Knowledge Base)

```
Documents → Chunking → Embedding → Vector DB Storage
```

**Step 1: Collect Your Data**

- Documentation (Markdown, PDFs)
- Internal wikis
- Customer support tickets
- Product databases
- Code repositories

**Step 2: Chunk It**  
Break large documents into smaller pieces (chunks). Why? LLMs need focused context, not entire manuals.

**Step 3: Embed It**  
Convert each chunk into a vector using an embedding model (OpenAI Ada, Sentence-BERT, etc.)

**Step 4: Store It**  
Index vectors in a vector database with metadata (source, timestamp, category)

### Phase 2: Retrieval (Finding Relevant Knowledge)

```
User Query → Embed Query → Search Vector DB → Retrieve Top-K Chunks
```

When a user asks a question:

1. Convert their question into an embedding
2. Search your vector DB for similar chunks
3. Retrieve the top 3-10 most relevant pieces
4. (Optional) Rerank results for precision

### Phase 3: Generation (Creating the Answer)

```
Query + Retrieved Context → LLM → Grounded Answer
```

Construct a prompt:

```
Context: [Retrieved chunks]
Question: [User query]
Instructions: Answer based only on the context provided.
```

The LLM generates a response grounded in your actual data.

[![Image about RAG](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fsjypval488xir5tt7q68.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fsjypval488xir5tt7q68.png)

---

## My First RAG System (The One That Actually Worked)

After the course, I wanted to build the simplest possible RAG system to prove I understood it. Here's what I came up with—about 50 lines of Python (Which ran really slow in my Macbook):

```
# requirements: sentence-transformers, faiss-cpu, openai

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import openai

# Step 1: Prepare documents
documents = [
    "Our refund policy: 30 days, full refund with receipt.",
    "Shipping takes 3-5 business days for domestic orders.",
    "We accept Visa, Mastercard, and PayPal.",
    "Customer support: support@example.com or call 1-800-HELP"
]

# Step 2: Create embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim embeddings
embeddings = model.encode(documents)

# Step 3: Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

# Step 4: Retrieval function
def retrieve(query, k=2):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k)
    return [documents[i] for i in indices[0]]

# Step 5: RAG function
def rag_query(question):
    # Retrieve relevant docs
    context = retrieve(question)

    # Create prompt
    prompt = f"""Answer the question based only on this context:

Context:
{chr(10).join(context)}

Question: {question}

Answer:"""

    # Generate response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# Test it
print(rag_query("How long does shipping take?"))
# Output: "Shipping takes 3-5 business days for domestic orders."
```

**What just happened?**

1. I embedded 4 documents using a lightweight model I could run locally (22MB download)
2. Stored them in FAISS—this took me 10 minutes to figure out from the docs
3. When asked about shipping, the system found the right document
4. Fed it to GPT-3.5 to generate a natural answer

**Results:** Optimized token usage. Zero hallucinations. I was hooked.

This tiny example taught me more than hours of coursework. Seeing retrieval work in real-time made everything click.

---

## Chunking: The Part That Took Me the Longest to Get Right

The course covered chunking in one lecture. In practice, it took me three weeks of experimentation. Here's what I learned the hard way:

### 1\. Fixed-Size Chunking (Beginner-Friendly)

Split every N tokens (e.g., 512 tokens) with optional overlap:

```
def chunk_fixed(text, chunk_size=512, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks
```

**Pros:** Simple, predictable  
  
**Cons:** May split mid-sentence, breaks semantic units

**Use when:** You have clean, uniform text (articles, docs)

### 2\. Semantic Chunking (Intermediate)

Split at natural boundaries (paragraphs, sections, sentences):

```
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", " "]  # Try these in order
)

chunks = splitter.split_text(long_document)
```

**Pros:** Respects semantic boundaries  
  
**Cons:** Variable chunk sizes

**Use when:** You have structured documents (PDFs, articles)

### 3\. Hybrid Chunking (Advanced)

Combine approaches:

- Use section headers to define chunk boundaries
- Keep chunks within token limits
- Add metadata (section title, page number)

[![Chunking](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fzdi0y98iy0xz2ili615x.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fzdi0y98iy0xz2ili615x.png)

### What Actually Worked for Me:

✅ **Always use overlap** (I settled on 15%)—this fixed so many "half-answer" problems  
  
✅ **Metadata is your friend** —I can filter by date, source, document type  
  
✅ **Start with 512 tokens** —then adjust. I went up to 768 for technical docs  
  
✅ **Test with real queries** —what looks good in theory often fails in practice  
  
⚠️ **My biggest mistake:** Chunks too small (200 tokens). Context disappeared.

**My advice:** Don't overthink it at first. Use 512 tokens with 50 token overlap, then iterate based on what your users actually search for.

---

## Retrieval: What I Wish I'd Known Earlier

In the course, we learned semantic search (embeddings + vector similarity). In my projects, I discovered that wasn't always enough.

### 1\. Dense Retrieval (Semantic Search)

This is where I started: convert everything to vectors, find similar vectors.

**Best models (as of 2025):**

- `text-embedding-3-large` (OpenAI) - 1536 dims, excellent quality
- `all-MiniLM-L6-v2` (open source) - 384 dims, fast, good enough
- `bge-large-en-v1.5` (BAAI) - 1024 dims, top open source option

**Pros:** Captures semantic meaning, handles synonyms  
  
**Cons:** Computationally intensive

### 2\. Sparse Retrieval (BM25/TF-IDF)

Traditional keyword search. Fast, simple, explainable.

```
from rank_bm25 import BM25Okapi

corpus = [doc.split() for doc in documents]
bm25 = BM25Okapi(corpus)

query = "refund policy".split()
scores = bm25.get_scores(query)
top_doc = documents[np.argmax(scores)]
```

**Pros:** Fast, deterministic, good for exact keyword matches  
  
**Cons:** Misses semantic similarity ("car" won't match "automobile")

### 3\. Hybrid Search (Best of Both)

Combine dense and sparse retrieval:

```
def hybrid_search(query, alpha=0.5):
    # Get semantic results
    semantic_results = vector_db.search(query, k=20)

    # Get BM25 results
    bm25_results = bm25.search(query, k=20)

    # Merge with weighted scores
    combined = merge_results(
        semantic_results, 
        bm25_results, 
        alpha=alpha  # 0.5 = equal weight
    )

    return combined[:10]  # Top 10
```

**When to use hybrid:**

- Users search with specific keywords (product names, codes)
- Domain with technical jargon
- You need explainable results

| Method | Speed | Accuracy | Best For |
| --- | --- | --- | --- |
| Dense (Semantic) | Medium | High | Natural language queries |
| Sparse (BM25) | Fast | Medium | Keyword search |
| Hybrid | Medium | Highest | Production systems |

### 4\. Reranking: The Game-Changer I Almost Skipped

I almost didn't implement reranking. "Initial retrieval is good enough," I thought. Then I tried it:

```
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Initial retrieval: Get top 20
candidates = vector_db.search(query, k=20)

# Rerank: Score each candidate against query
scores = reranker.predict([(query, doc) for doc in candidates])

# Return top 5 after reranking
reranked = [candidates[i] for i in np.argsort(scores)[-5:]]
```

**My results:** Accuracy jumped from 73% to 89% on my test queries on test dataset in the course. I immediately noticed better answers.  
  
**Tradeoff:** Added some latency, which is totally worth it.

Reranking should became non-negotiable in my next projects.

## Vector Databases: My Journey From FAISS to Production

### Where I Started: Local and Simple

**1\. FAISS (Facebook AI Similarity Search)**

This was my first choice after the course. Why?

- **Dead simple:** Got it running in 30 minutes
- **Free:** Important when you're learning
- **Fast enough:** For my 10K documents

**The catch:** No persistence out of the box. I had to save/load the index manually. Fine for prototyping, annoying for production.

```
import faiss
index = faiss.IndexFlatL2(dimension)  # Brute force, exact search
index.add(embeddings)
```

**2\. LocalChromaDB**

- **Pros:** Simple, embedded mode, good for beginners
- **Cons:** Not optimized for large scale
- **Use for:** Side projects, MVPs, local development
```
import chromadb
client = chromadb.Client()
collection = client.create_collection("docs")
collection.add(documents=texts, embeddings=embeddings, ids=ids)
```

### Where I Moved for Production

**3\. Qdrant**

- **Pros:** Rust-based (fast), filtering, open source, good docs, for speech applications where latency matters
- **Cons:** Smaller community than others
- **Use for:** Production, performance-critical apps

**4\. Milvus/Zilliz**

- **Pros:** Built for massive scale (billions of vectors), battle-tested
- **Cons:** Complex setup, steeper learning curve
- **Use for:** Enterprise scale, billions of documents

| Database | Ease of Use | Scalability | Cost | Open Source | Best For |
| --- | --- | --- | --- | --- | --- |
| FAISS | ⭐⭐⭐⭐⭐ | ⭐⭐ | Free | ✅ | Learning, prototypes |
| ChromaDB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Free | ✅ | MVPs, small apps |
| Qdrant | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Free/$ | ✅ | Performance-critical |
| Milvus | ⭐⭐ | ⭐⭐⭐⭐⭐ | Free/$$$ | ✅ | Enterprise scale |

### My Recommendation Based on What I've Built:

- **Your first RAG project?** → FAISS. Get something working in an afternoon.
- **Building a side project?** → ChromaDB. Easy persistence, good docs.
- **Serious about production?** → Milvus or Qdrant. I've tried and tested both, both are solid.

---

## RAG vs Fine-Tuning: When to Use What

This is the million-dollar question.

| Criterion | RAG | Fine-Tuning |
| --- | --- | --- |
| **Cost** | Low (inference only) | High ($10K-$100K+) |
| **Update frequency** | Real-time | Requires retraining |
| **Setup time** | Days | Weeks/months |
| **Accuracy on facts** | Excellent (grounded) | Good (can hallucinate) |
| **Behavior modification** | Limited | Excellent |
| **Interpretability** | High (see sources) | Low (black box) |
| **Latency** | Slightly higher | Lower |

**Use RAG when:**

- Your data changes frequently
- You need factual accuracy with citations
- Budget is limited
- You need to explain answers (show sources)

**Use Fine-Tuning when:**

- You need to change model *behavior* (tone, format, style)
- Data is static
- Latency is critical
- Budget allows

**Best approach?** Hybrid: Fine-tune for behavior, RAG for knowledge.

[![Decision](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F79dqcnrnicwxm86edpzr.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F79dqcnrnicwxm86edpzr.png)

---

## The Surprise: Small Models + RAG Beat GPT-4

This wasn't in the course, but it's the most important thing I've learned:

**A well-tuned 7B model with RAG beats GPT-4 for domain-specific tasks.**

I didn't believe it until I tried it in my demo project. Here's why it works:

1. **Specialized Retrieval beats General Knowledge**
	- GPT-4 knows a little about everything
		- Your RAG knows *everything* about your domain
2. **Smaller Models are Faster**
	- Llama-3 8B: ~50ms inference
		- GPT-4: ~500ms inference
		- 10x speed improvement
3. **Cost Savings are Dramatic**
```
GPT-4: $0.03 per 1K tokens
Llama-3 8B (self-hosted): $0.0001 per 1K tokens
300x cheaper
```
1. **You Control the Infrastructure**
	- No vendor lock-in
		- Data privacy guaranteed
		- Custom optimizations

### My Experience:

**Project 1: Documentation Chatbot**

- Started with GPT-4: Great answers
- Switched to Llama-3 8B + RAG: Better answer
- **The difference:** GPT-4 would paraphrase incorrectly. Llama-3 + RAG quoted exact docs.

**Project 2: Customer Support Bot**

- Tried GPT-4 first: Some of queries handled correctly (67%)
- Moved to Llama-3.2 8B + RAG: 91% accuracy
- **Why:** RAG retrieved the exact support article. Model just had to summarize it.

**Project 3: Internal Knowledge Assistant**

- Using Phi-3 3.8B (tiny model) + aggressive Hybrid search RAG
- Responses in 120ms average
- I prefer it over standalone GPT-4 system

---

## Where I Think This Is Heading

After three projects and countless experiments, here's what I believe:

As smaller models get better (and they are—fast), RAG becomes the great equalizer. We're moving toward:

- **Specialized beats generalized** for most business use cases
- **Open source + RAG** is the default architecture
- **Cost per query** drops from dollars to fractions of cents
- **Every company** runs their own domain-expert AI

### Emerging Trends: Agentic RAG

The next evolution is **Agentic RAG** - systems that don't just retrieve and generate, but reason about *what* to retrieve and *when*:

**How Agentic RAG works:**

1. **Query Analysis:** Agent determines if it needs more information
2. **Multi-Step Retrieval:** Performs multiple retrieval rounds, refining based on initial results
3. **Tool Use:** Can call external APIs, run code, or query structured databases
4. **Self-Reflection:** Evaluates its own answers and retrieves more if unsure
```
# Example: Agentic RAG flow
def agentic_rag(query):
    # Step 1: Analyze query complexity
    if needs_multi_step_reasoning(query):
        # Step 2: Break down into sub-questions
        sub_queries = decompose_query(query)

        # Step 3: Retrieve for each sub-question
        contexts = [retrieve(q) for q in sub_queries]

        # Step 4: Synthesize and verify
        answer = generate_with_verification(query, contexts)

        # Step 5: If confidence is low, retrieve more
        if answer.confidence < 0.8:
            additional_context = retrieve_with_feedback(query, answer)
            answer = generate_final(query, contexts + additional_context)
    else:
        # Simple single-step RAG
        answer = simple_rag(query)

    return answer
```

**Benefits of Agentic RAG:**

- **Better accuracy** on complex queries requiring multi-hop reasoning
- **Adaptive retrieval** - only retrieves what's needed
- **Explainable reasoning** - can show the step-by-step process
- **Cost-efficient** - avoids over-retrieving

**Real-world impact:** Agentic RAG systems have shown 30-40% improvement over traditional RAG on complex question-answering benchmarks like HotpotQA and MultiHop-RAG.

**My take:** Most companies don't need latest GPT-5. They need their own data, smart retrieval, and a well-implemented RAG system. That's 90% of the value at 10% of the cost.

This realization changed how I think about AI engineering entirely.

---

## Production Lessons: What I'm Learning

### 1\. Monitoring Saved Me

I didn't add monitoring in my first project. Big mistake. In my second project, I tracked the context, but from other souces I've learned that:

**Retrieval Metrics:**

- **Recall@K:** Are the right docs in top K results?
- **Precision@K:** What % of retrieved docs are relevant?
- **MRR (Mean Reciprocal Rank):** How far down is the first relevant result?

**Generation Metrics:**

- **Faithfulness:** Does answer align with retrieved context?
- **Relevance:** Does answer address the question?
- **Latency:** Time from query to response

**Business Metrics:**

- User satisfaction (thumbs up/down)
- Resolution rate (for support chatbots)
- Cost per query
```
# Simple evaluation framework
def evaluate_rag(query, ground_truth, rag_system):
    # Retrieval
    retrieved_docs = rag_system.retrieve(query)
    recall = calculate_recall(retrieved_docs, ground_truth_docs)

    # Generation
    answer = rag_system.generate(query, retrieved_docs)
    faithfulness = check_faithfulness(answer, retrieved_docs)

    return {"recall": recall, "faithfulness": faithfulness}
```

### 2\. Handling Context Overflow

What if retrieved context exceeds LLM's window?

**Solutions:**

- **Summarize chunks** before passing to LLM
- **Use longer context models** (Claude 3 200K)
- **Implement multi-hop retrieval** (iterative refinement)
- **Compress context** with extractive summarization

### 3\. Cost Optimization

**Embedding costs:**

- Cache embeddings (don't recompute for same text)
- Use cheaper models for preliminary retrieval
- Batch embed operations

**LLM costs:**

- Use smaller models where accuracy permits
- Implement caching for common queries
- Set max\_tokens to avoid runaway generation

**Infrastructure:**

- Self-host embeddings model (one-time cost)
- Use spot instances for batch processing
- Implement request throttling

### 4\. Multi-Tenancy Patterns

For SaaS products:

```
# Namespace approach
collection.add(
    documents=docs,
    embeddings=embeddings,
    metadata=[{"tenant_id": "customer_123"}]
)

# Query with filter
results = collection.query(
    query_embedding=query_emb,
    filter={"tenant_id": "customer_123"}
)
```

### 5\. Incremental Updates

Don't rebuild your entire index daily:

```
# Add new documents
new_docs = fetch_new_documents(since=last_update)
new_embeddings = model.encode(new_docs)
index.add(new_embeddings)

# Update existing documents
updated_docs = fetch_updated_documents()
# Delete old versions, add new versions
for doc in updated_docs:
    index.remove(doc.old_id)
    index.add(doc.new_embedding, doc.new_id)
```

[![Prod](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fplle9rpdhjuj5tj1irx5.png)](https://media2.dev.to/dynamic/image/width=800%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fplle9rpdhjuj5tj1irx5.png)

---

## Mistakes I Made or would have made (So You Don't Have To)

### ⚠️ Mistake 1: Chunking Too Small

**What I did:** Started with 128-token chunks to "maximize precision"  
  
**What happened:** Retrieval found fragments without enough context. Answers were incomplete.  
  
**Fix:** Bumped to 512 tokens with 15% overlap. Immediately better.

### ⚠️ Mistake 2: Ignoring Metadata

**What I did:** Pure semantic search, no filters  
  
**What happened:** Retrieved old documentation when new versions existed  
  
**Fix:** Added timestamp and version filters. Game changer.

```
results = vector_db.search(
    query=query,
    filter={"category": "product_docs", "date": {"$gte": "2024-01-01"}}
)
```

### ⚠️ Mistake 3: Not Profiling Latency

**What I did:** Assumed "fast enough" without measuring  
  
**What happened:** Users complained about 3-second response times  
  
**Fix:**

- Profiled every step: embedding (50ms), retrieval (80ms), reranking (200ms), generation (2.1s)
- Optimized generation by switching models
- Got down to 800ms total

### ⚠️ Mistake 4: Trusting Retrieval Blindly

**What I did:** Always passed top results to LLM, no quality check  
  
**What happened:** When retrieval failed, LLM made stuff up  
  
**Fix:** Added confidence thresholds:

```
def rag_with_fallback(query):
    results = retrieve(query, k=3)

    # Check if top result is confident
    if results[0].score < 0.7:  # Low confidence
        return "I don't have enough information to answer this."

    return generate(query, results)
```

### ⚠️ Mistake 5: "Set It and Forget It"

**What I did:** Built the system, deployed it, moved on  
  
**What happened:** After adding 5000 more documents, retrieval quality dropped 15%  
  
**Fix:** My plan will be to run evaluation tests occasionally. Catch degradation early.

---

## Frequently Asked Questions

**Q: Do I need a vector database or can I use a traditional DB?**  
  
A: For <10K documents, you can get away with FAISS or even numpy arrays. Beyond that, a proper vector DB gives you scalability, filtering, and performance.

**Q: What's the minimum viable RAG system?**  
  
A: 50 lines of Python (see the example above), a free embedding model, and FAISS. Total cost: $0 to start.

**Q: How do I handle PDF extraction and preprocessing?**  
  
A: Use libraries like `pymupdf`, `pdfplumber`, or `unstructured`. Watch out for table extraction—it's tricky.

**Q: Can I do RAG with completely private/offline models?**  
  
A: Absolutely. Use `sentence-transformers` for embeddings and `llama.cpp` or `ollama` for local LLM inference.

**Q: What about structured data (databases, spreadsheets)?**  
  
A: Convert to text descriptions or use hybrid approaches (SQL + RAG). Example: Generate natural language descriptions of database rows.

**Q: How do I know if my chunking strategy is working?**  
  
A: Measure retrieval metrics. If recall is low, experiment with different chunk sizes and overlap.

**Q: Should I use multiple embedding models?**  
  
A: For specialized domains (code, legal, medical), domain-specific embeddings often outperform general-purpose ones.

**Q: What about multi-modal RAG (images, tables, charts)?**  
  
A: Use multi-modal embedding models like CLIP (for images) or convert tables to text. It's an active area of research.

---

## What I Wish I Knew Before Starting

If I could go back and tell myself these things before building my first RAG system:

### The Core Insights:

1. **RAG separates reasoning from knowledge** → LLMs handle reasoning, databases handle facts
2. **The pipeline is simple:** Ingest → Chunk → Embed → Store → Retrieve → Generate
3. **Chunking matters:** Start with 512 tokens, add overlap, respect semantic boundaries
4. **Hybrid search beats pure semantic:** Combine BM25 + vector search for best results
5. **Small models + RAG can beat GPT-4** on domain-specific tasks at 1/100th the cost
6. **Production is about monitoring:** Track retrieval quality, latency, and cost
7. **Start simple, optimize later:** FAISS + OpenAI embeddings + GPT-3.5 gets you 80% there
8. **Agentic RAG is the future:** Multi-step reasoning and adaptive retrieval unlock new capabilities

### Why I'm Excited About This:

- **Accessibility:** I am trying to build production AI with decent ML background. Just a curiosity and determination.
- **Economics:** RAG systems cost 1-5% of what pure LLM solutions would cost
- **Reliability:** Users trust answers because they see sources. No more "did the AI make this up?"
- **Agility:** I can update knowledge in minutes. No retraining, no waiting.

### The Future of RAG:

We're moving toward:

- **Adaptive RAG:** Systems that adjust retrieval strategy based on query complexity
- **Agentic RAG:** Multi-step reasoning with dynamic retrieval and tool use
- **Fusion models:** Architectures that blend parametric and non-parametric knowledge
- **Smaller, smarter retrievers:** Specialized models optimized for retrieval

**Bottom line:** RAG isn't just a technique—it's the architecture that makes practical, affordable, trustworthy AI possible.

---

## Our Next Steps

Choose your adventure based on experience level:

### 🌱 Beginners:

1. ✅ Implement the 50-line minimal RAG example above
2. ✅ Experiment with different chunk sizes (256, 512, 1024)
3. ✅ Try different embedding models (compare results)
4. ✅ Build a chatbot for a small document set (10-100 docs)
5. 📚 Read: [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)

### 🚀 Intermediate (I still have to implement few of em):

1. ✅ Implement evaluation metrics (recall@K, faithfulness)
2. ✅ Set up a production vector DB (Weaviate or Qdrant)
3. ✅ Add hybrid search (BM25 + semantic)
4. ✅ Implement reranking
5. ✅ Experiment with smaller models (Llama-3 8B, Mistral 7B)
6. 📚 Read: [RAG Evaluation Best Practices](https://arxiv.org/abs/2312.10997)

### ⚡ Advanced (I'm aiming for this nex):

1. ✅ Build multi-tenant RAG system with namespace isolation
2. ✅ Implement adaptive retrieval strategies
3. ✅ Optimize for sub-100ms latency
4. ✅ Run cost analysis and optimize for $0.0001/query
5. ✅ Build agentic RAG with multi-step reasoning
6. ✅ Contribute to open source RAG frameworks
7. 📚 Read: [Advanced RAG Techniques](https://arxiv.org/abs/2401.15884)

### 🎯 RAG Journey Checklist:

- \[ \] Understand embeddings and vector similarity
- \[ \] Build minimal RAG system (FAISS + OpenAI)
- \[ \] Implement chunking strategy for your use case
- \[ \] Set up production vector database
- \[ \] Add evaluation metrics
- \[ \] Implement hybrid search
- \[ \] Optimize for cost and latency
- \[ \] Deploy to production
- \[ \] Monitor and iterate
- \[ \] Explore agentic RAG patterns

---

## Resources and Further Reading

## Essential Links:

### Vector Databases

### Primary Options (Recommended)

- **[Milvus Documentation](https://milvus.io/docs)** - Distributed vector DB with GPU support
- **[Qdrant Documentation](https://qdrant.tech/documentation/)** - Production-ready vector DB with cloud SaaS option
- **[ChromaDB Documentation](https://docs.trychroma.com/)** - Lightweight, Python-first vector database

---

## Embedding Models & Evaluation

### MTEB Leaderboard & Model Selection

- **[MTEB Leaderboard (English)](https://huggingface.co/spaces/mteb/leaderboard)** - Compare 100+ embedding models across 56+ tasks
- **[MTEB Leaderboard (Multi-lingual)](https://huggingface.co/spaces/mteb/leaderboard-multilingual)** - Multilingual model comparison

### Top Opensource Embedding Models

- **Qwen3-Embedding-8B** - State-of-the-art (Dec 2024), multilingual support
- **jina-embeddings-v3** - 570M params, 8K context length, task-specific LoRA
- **NV-Embed-v2** - NVIDIA's top performer, #1 on MTEB (Aug 2024)
- **bge-m3** - BAAI's versatile model, dense + sparse + multi-vector retrieval
- **arctic-embed-l** - Open-source, outperforms Cohere embed-v3

### Framework-Specific Resources

- **[HuggingFace Sentence Transformers](https://www.sbert.net/)** - Python library for semantic embeddings
- **[OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)** - Production embedding service

### Domain-Specific Embeddings

- **Medical**: PubMedBERT (biomedical literature), BioLORD
- **Finance**: Finance-Embeddings, BGE-Financial, Voyage Finance
- **Code**: Code embeddings from GitHub, CodeBERT

---

## RAG Frameworks & Orchestration

### Core Frameworks (Production-Ready)

- **[LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/overview)** - Graph-based agentic workflows with stateful execution (2024+)
- **[LlamaIndex Documentation](https://docs.llamaindex.ai/)** - Agent-powered context augmentation with LlamaParse document parsing
- **[Haystack Documentation](https://haystack.deepset.ai/)** - v2.0+ with explicit RAG pipelines and evaluation tools
- **[LangChain Documentation](https://python.langchain.com/docs/)** - Rapid prototyping and experimentation

### Emerging & Specialized

- **[Pathway Real-time RAG](https://pathway.com/developers/user-guide/llm-xpack/llm-app-pathway/)** - Streaming data processing for live RAG updates (2025)
- **[DSPy Documentation](https://github.com/stanfordnlp/dspy)** - Declarative pipeline programming for LLMs
- **[Cohere Agent Framework](https://docs.cohere.com/docs/agents)** - Multi-agent orchestration with built-in tools

---

## Advanced RAG Approaches

### Graph-Enhanced & Hierarchical RAG

- **[GraphRAG (Microsoft Research)](https://microsoft.github.io/graphrag/)** - LLM-derived knowledge graphs with v1.0 release (Dec 2024)
	- Latest: LazyGraphRAG (Nov 2024) - cost-efficient variant without pre-summarization
		- [GraphRAG GitHub](https://github.com/microsoft/graphrag)
- **[LightRAG Framework](https://github.com/HKUDS/LightRAG)** - Graph-enhanced with dual-level retrieval & incremental updates (2024)
	- Paper: [LightRAG: Simple and Fast Retrieval-Augmented Generation](https://arxiv.org/abs/2410.05779)
- **[ArchRAG](https://arxiv.org/pdf/2502.09891.pdf)** - Attributed community-based hierarchical RAG (Feb 2025)

### Hierarchical & Long-Context

- **[RAPTOR Framework](https://arxiv.org/abs/2311.04253)** - Recursive abstractive processing for tree-organized retrieval
	- Implementation: [RAGFlow's RAPTOR Implementation](https://ragflow.io/blog/long-context-rag-raptor)
- **[RAG-Anything](https://arxiv.org/html/2510.12323)** - Multimodal RAG supporting text, images, tables, equations (2024)

### Self-Correcting & Agentic RAG

- **[Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511)** - Adaptive retrieval with quality scoring
- **[Agentic RAG Frameworks (2025)](https://alphacorp.ai/top-5-rag-frameworks-november-2025/)** - Overview of LangGraph, Haystack, LlamaIndex, Pathway, DSPy

---

## RAG Evaluation & Benchmarking

### Evaluation Frameworks

- **[RAGAS (Retrieval-Augmented Generation Assessment)](https://github.com/explodinggradients/ragas)** - Reference-free RAG evaluation with metrics like context precision, entity recall, faithfulness
	- [RAGAS Paper](https://arxiv.org/abs/2309.15217)
		- [Evaluating RAG with RAGAS Tutorial](https://www.youtube.com/watch?v=-69Fx8F9ma4)
- **[BEIR Benchmark](https://github.com/beir-cellar/beir)** - Retrieval evaluation across heterogeneous datasets

### Research Papers & Benchmarks

- **[Original RAG Paper: Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)** - Foundational work
- **[REALM: Retrieval-Augmented Language Model Pre-Training](https://arxiv.org/abs/2002.08909)** - Pre-training with retrieval
- **[Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)** - Dense vector retrieval fundamentals
- **[BRIGHT Benchmark](https://arxiv.org/abs/2407.12883)** - Reasoning-intensive retrieval evaluation (2024)

---

## Research Papers (Foundational & Recent)

### Core RAG Papers

- [RAG: Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)
- [REALM: Retrieval-Augmented Language Model Pre-Training](https://arxiv.org/abs/2002.08909)
- [Dense Passage Retrieval](https://arxiv.org/abs/2004.04906)
- [Self-RAG: Learning to Retrieve, Generate, and Critique](https://arxiv.org/abs/2310.11511)

### Recent Advances (2024-2025)

- [LightRAG: Simple and Fast Retrieval-Augmented Generation](https://arxiv.org/abs/2410.05779)
- [RAG-Anything: All-in-One RAG Framework](https://arxiv.org/html/2510.12323)
- [TigerVector: Vector Search in Graph Databases](https://arxiv.org/abs/2501.11216)
- [ArchRAG: Attributed Community-based Hierarchical RAG](https://arxiv.org/pdf/2502.09891.pdf)
- [RAPTOR: Recursive Abstractive Processing](https://arxiv.org/abs/2311.04253)

### Embedding Model Papers

- [NV-Embed: Improved Techniques for Training LLMs as Embedding Models](https://arxiv.org/abs/2405.17428)
- [Arctic-Embed: Scalable, Efficient, and Accurate Text Embedding](https://arxiv.org/abs/2405.05374)
- [jina-embeddings-v3: Multilingual Embeddings With Task LoRA](https://arxiv.org/abs/2409.10173)
- [LEAF: Knowledge Distillation of Text Embedding Models](https://arxiv.org/abs/2509.12539)

### Vector Database Papers

- [Vector Database Management Systems: Concepts & Challenges](https://arxiv.org/abs/2309.11322)
- [VDTuner: Automated Performance Tuning for Vector Data Management](https://arxiv.org/abs/2404.10413)
- [Curator: Efficient Indexing for Multi-Tenant Vector Databases](https://arxiv.org/abs/2401.07119)

---

## Community & Support

### Forums & Discussion

- **[r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/)** - Open-source LLM and RAG community
- **[LangChain Fourm](https://forum.langchain.com/)** - Active community support

### Blogs & Learning

- **[Microsoft GraphRAG Blog](https://www.microsoft.com/en-us/research/project/graphrag/)** - Official GraphRAG research updates
- **[LangChain Blog](https://blog.langchain.dev/)** - Framework updates and tutorials
- **[Milvus Blog](https://milvus.io/blog)** - Vector DB best practices

---

## Final Thoughts from the Trenches

Few months ago, I know nothing about RAG and started to learn more about it. Today, I'm iming to build production RAG after understanding the RAG concepts which will aims to provide accurate answers.

The biggest lesson? **RAG isn't just a technique—it's a different way of thinking about AI.**

Instead of "how can I make the model smarter," I now ask "how can I give it better information?" That mental shift unlocked everything.

The course taught me the foundations. Building real systems taught me the craft. The gap between those two was wider than I expected, but crossing it was incredibly rewarding.

If you're where I was three months ago—course completed, wondering what's next—my advice is simple: **Build something. Ship it. Learn from real users.**

Your first RAG system won't be perfect. Mine wasn't. But it'll teach you more than any tutorial ever could.

**The best time to start was yesterday. The second best time is now.**

---

*If you're building RAG systems, I'd love to hear about your experience. What surprised you? What worked? What didn't? Drop a comment—let's learn from each other.*

*This Article written on December 2025, based on my hands-on experience building RAG systems. The field moves fast—always test and validate for your specific use case.*

[![Tiger Data image](https://media2.dev.to/dynamic/image/width=775%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fi.imgur.com%2FJQ1vwsm.png)](https://www.tigerdata.com/blog/agent-memory-search-problem-not-storage-problem?utm_source=content-syndication&utm_medium=referral&utm_campaign=dev-to&utm_content=tiger_mcp_workshopagent_memory_blog&bb=264676)

## Agent Memory Is a Search Problem, Not a Storage Problem ❌

Long-term conversational memory is the ability to recall and reason over months of past conversations. It is one of the hardest unsolved problems in AI assistants, and the field has converged on a shared assumption about how to solve it.
