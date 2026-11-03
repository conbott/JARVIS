# Jarvis Project Documentation: End-to-End Technical Report

This document provides a comprehensive, granular, and accurate account of all architectural decisions, implementations, features, algorithms, optimizations, and troubleshooting completed for the **Jarvis Local RAG & Voice Assistant** project.

---

## Table of Contents
1. [Project Overview & Design Philosophy](#1-project-overview--design-philosophy)
2. [Branding & User Interface](#2-branding--user-interface)
3. [Hardware Detection & Dynamic Model Management](#3-hardware-detection--dynamic-model-management)
4. [Document Ingestion & Processing Pipeline](#4-document-ingestion--processing-pipeline)
5. [Hybrid Query Routing & Intent Classification](#5-hybrid-query-routing--intent-classification)
6. [Vector Retrieval & The Spread Retrieval Algorithm](#6-vector-retrieval--the-spread-retrieval-algorithm)
7. [Real-Time Web Search & Query Reformulation](#7-real-time-web-search--query-reformulation)
8. [Anti-Hallucination & System Clock Ground Truth](#8-anti-hallucination--system-clock-ground-truth)
9. [Multi-Provider LLM & Embedding Architecture](#9-multi-provider-llm--embedding-architecture)
10. [Dual Vector Store Tiers: ChromaDB & Pinecone](#10-dual-vector-store-tiers-chromadb--pinecone)
11. [Bidirectional Push-to-Talk Voice Pipeline](#11-bidirectional-push-to-talk-voice-pipeline)
12. [Server-Sent Events (SSE) Streaming Protocol](#12-server-sent-events-sse-streaming-protocol)
13. [Security, Rate Limiting & Proxy Compatibility](#13-security-rate-limiting--proxy-compatibility)
14. [Deployment: Local & Cloud Topologies](#14-deployment-local--cloud-topologies)
15. [Automated Scripts (setup.bat, start_all.bat, stop_all.bat)](#15-automated-scripts-setupbat-start_allbat-stop_allbat)
16. [Verification History & Resolved Challenges](#16-verification-history--resolved-challenges)

---

## 1. Project Overview & Design Philosophy

Jarvis is a private, offline-capable, full-stack Local Retrieval-Augmented Generation (RAG) and Voice Assistant. The project was engineered around four foundational principles:

1. **Zero-Cost, Privacy-First Local Operation**: By default, the application runs entirely on the host machine using Ollama for local LLM inference (`qwen2.5-coder:7b`) and local dense vector embeddings (`qwen3-embedding:0.6b`), ChromaDB for on-disk vector persistence, `faster-whisper` for local CPU speech-to-text, and Edge-TTS for local voice synthesis. Zero user data leaves the machine in default mode.
2. **Dual-Mode Cloud Scalability**: The entire codebase seamlessly switches to cloud-hosted operation (Google Gemini, OpenAI, Pinecone) simply by toggling environment variables, without changing frontend or backend business logic.
3. **Strict Citation Grounding**: The assistant cites page numbers, filenames, and cosine similarity scores for document retrieval, and URLs and domains for web search fallback.
4. **Resilient Conversational Continuity**: Multi-turn dialogue context is maintained with intelligent pronoun reformulation, date detection, and thinking-block filtering.

---

## 2. Branding & User Interface

### A. Nature-Tinted Claude Dark Palette
The frontend is built with React 19, Vite, and Tailwind CSS v4, adhering to a nature-green dark aesthetic:
- **Background Root**: `#121813` (Deep Forest Black)
- **Surfaces & Cards**: `#1a221b` (Subtle Forest Moss)
- **Border Accents**: `#2e3b30` / `#3d4f40`
- **Primary Text**: Newsreader serif typography for assistant answers, Inter for UI controls, and JetBrains Mono for code blocks.
- **Accent Green**: `#a8d5a2` (Soft Sage)

### B. Custom Jarvis HUD Icon & Branding
- Extracted high-resolution circular HUD emblem with anti-aliasing from wallpaper artwork.
- Placed at `frontend/public/jarvis.png` and `frontend/public/favicon.png`.
- Configured as the header avatar, welcome screen emblem, and browser tab favicon.
- Browser title standardized to `Jarvis`.

---

## 3. Hardware Detection & Dynamic Model Management

### A. Automated Hardware Discovery (`backend/services/hardware_service.py`)
On application initialization, the backend probes host hardware specifications:
- **CPU**: Core count, clock speed, and architecture via `platform` and `psutil`.
- **System RAM**: Total and available RAM in gigabytes.
- **GPU & VRAM**: Inspects NVIDIA CUDA devices via `torch.cuda` / `pynvml`, Apple Silicon unified memory via `torch.backends.mps`, and Intel Arc / CPU fallbacks.

### B. Hardware Tier Recommendation Matrix
Based on detected hardware, Jarvis recommends the optimal Ollama LLM:

| Hardware Tier | Detected Specs | Recommended LLM | Parameters | Memory Footprint | Pull Command |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Entry / CPU** | CPU Only or VRAM < 6GB | `llama3.2:3b` | 3 Billion | ~2.5 GB RAM | `ollama pull llama3.2:3b` |
| **Mid-Tier (Default)** | 6GB – 10GB VRAM (e.g. RTX 3060, 4060) | `qwen2.5-coder:7b` | 7 Billion | ~5.0 GB VRAM | `ollama pull qwen2.5-coder:7b` |
| **High-End** | 12GB+ VRAM or Apple Silicon 16GB+ | `qwen2.5-coder:14b` | 14 Billion | ~9.0 GB VRAM | `ollama pull qwen2.5-coder:14b` |
| **Dense Embedding** | All Configurations | `qwen3-embedding:0.6b` | 596 Million | ~0.6 GB RAM | `ollama pull qwen3-embedding:0.6b` |

### C. In-App Model Switching (`/api/models/select`)
- Users can switch active models on the fly through the **System Panel** (top-right gear icon) without restarting the server or terminal.
- The endpoint updates `settings.LLM_MODEL` in runtime memory and instantly refreshes the active model indicator in the header.
- If a user prompts a model that has not been downloaded yet, the backend catches the HTTP 404 from Ollama and returns a helpful chat bubble with the exact `ollama pull <model>` command.

---

## 4. Document Ingestion & Processing Pipeline

The ingestion engine (`backend/routers/documents.py`) leverages LangChain for parsing and chunking:

1. **Format Support**: Uploads accept PDF (`.pdf`), plaintext (`.txt`), and Markdown (`.md`).
2. **Metadata-Preserving Parsing**:
   - `PyPDFLoader` extracts text page-by-page, assigning 1-based `page` numbers, `filename`, and `source_type: "document"`.
   - `TextLoader` processes UTF-8 encoded text and markdown documents.
3. **Recursive Character Chunking**:
   - Uses `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)`.
   - Splits hierarchically across double newlines, single newlines, and sentence breaks to preserve cohesive paragraphs.
4. **Vector Embedding**:
   - Chunks are embedded in batches via the configured embedding provider (Ollama `qwen3-embedding:0.6b`, Gemini `text-embedding-004`, or OpenAI `text-embedding-3-small`).
   - Vectors and metadata payloads are persisted to the active vector database (ChromaDB or Pinecone).

---

## 5. Hybrid Query Routing & Intent Classification

Jarvis uses an adaptive query routing engine (`backend/core/rag_chain.py`):

```
User Query ──> [Pre-Checks]
                   ├─ System Date/Time Query ──> Return Local Clock Ground Truth
                   ├─ Casual Conversation ─────> Direct LLM Stream (No Retrieval)
                   │
               [Search Mode Evaluation]
                   ├─ "web" Mode  ─────────────> DuckDuckGo Search
                   ├─ "docs" Mode ─────────────> Document Retrieval Only
                   └─ "auto" Mode ─────────────> [Intent Classifier]
                                                     ├─ Summary Intent  ──> Spread Retrieval
                                                     └─ Specific Query  ──> Similarity Search
                                                                                ├─ Score >= 0.35 ──> Grounded Doc Answer
                                                                                └─ Score < 0.35  ──> Web Fallback
```

### Modes:
- **`auto`**: Default mode. Bypasses retrieval for casual conversation, triggers spread retrieval for summaries, tests cosine similarity against `0.35`, and falls back to web search when no relevant document match exists.
- **`web`**: Direct real-time search. Bypasses document collections and queries DuckDuckGo for live internet sources and snippets.
- **`docs`**: Strict document grounding. Confines answers strictly to uploaded files without ever querying external search engines.

---

## 6. Vector Retrieval & The Spread Retrieval Algorithm

### A. Cosine Similarity Metric & Threshold
- ChromaDB returns cosine distance values $D \in [0, 2]$. These are transformed to cosine similarity via:
  $$\text{similarity} = 1.0 - D$$
- Mathematically, cosine similarity spans the interval $[-1.0, 1.0]$. Orthogonal or divergent chunks yield zero or negative similarity scores.
- A threshold of $\ge 0.35$ cleanly filters out irrelevant, orthogonal, or negative matches.

### B. The Spread Retrieval Algorithm for Document Summaries
Standard top-$k$ similarity fails on broad summary requests (*"summarize this document"*, *"what are the key takeaways"*) because summary semantics span the entire text rather than concentrating in one dense passage.

Jarvis implements **Spread Retrieval**:
1. **Reference Section Filtering**: Filters out chunks with high citation densities (`[1]`, `[2]`, `et al.`, `references`, `bibliography`).
2. **Abstract Inclusion**: Guarantees inclusion of the opening structural chunk (abstract / introduction).
3. **Conclusion Inclusion**: Guarantees inclusion of the final substantive content chunk (discussion / conclusions).
4. **Uniform Strided Sampling**: Samples evenly across intermediate pages up to the requested spread budget (default 8 chunks).
5. **SSE Emission**: Emits `"retrieval": "spread"` in the sources payload; the frontend displays clean document badges without misleading point-similarity percentages.

---

## 7. Real-Time Web Search & Query Reformulation

### A. DuckDuckGo Search Integration (`backend/core/search.py`)
- Executes queries via `duckduckgo_search` (`DDGS`).
- Cleans and strips search operators (`site:`, `filetype:`, punctuation noise).
- Extracts clean titles, target URLs, and contextual body snippets.
- Dispatches top search sources in the SSE payload for transparent user verification.

### B. Multi-Turn Conversational Query Reformulation
When users ask follow-up questions with pronouns (*"when was it first released"*, *"who is the current lead developer"*):
- The reformulation prompt inspects the last 3 conversational turns.
- It extracts the root entity (e.g. *"Pokémon Fire Ash"*) while deliberately ignoring transient sub-version noise (e.g. *"v3.7.1 update"*).
- Generates an unambiguous, standalone search query targeting the core question.

---

## 8. Anti-Hallucination & System Clock Ground Truth

To eliminate LLM date hallucinations (such as outputting `[insert today's date]` or repeating previous search failures):

1. **System Clock Fast Path**:
   - Broad regex pattern (`what('s| is) the (current )?(date|time|day|year)...`) catches date/time requests.
   - Responds deterministically using host local time: `datetime.now()`.
   - Bypasses external search entirely for date queries.
2. **Temporal Grounding in Search Prompts**:
   - When external search is triggered, the current host date and time are dynamically injected into the system prompt:
     `"Today's date is Tuesday, November 03, 2026. Use this to determine relative time expressions like 'latest' or 'current'."`
3. **Flexible Synthesis Instructions**:
   - System prompts instruct the LLM to synthesize available evidence from multiple sources rather than mechanically repeating rigid fallback scripts.

---

## 9. Multi-Provider LLM & Embedding Architecture

The core inference layer (`backend/core/llm.py` and `backend/core/embeddings.py`) provides unified abstractions:

| Provider | LLM Implementation | Embedding Implementation | Default Models |
| :--- | :--- | :--- | :--- |
| **Ollama** (Local) | HTTP streaming via `httpx` (`/api/chat`) | `OllamaEmbeddings` via LangChain | `qwen2.5-coder:7b` / `qwen3-embedding:0.6b` |
| **Google Gemini** (Cloud) | `ChatGoogleGenerativeAI` | `GoogleGenerativeAIEmbeddings` | `gemini-2.0-flash` / `text-embedding-004` |
| **OpenAI** (Cloud) | `ChatOpenAI` | `OpenAIEmbeddings` | `gpt-4o-mini` / `text-embedding-3-small` |
| **Generic OpenAI** | `ChatOpenAI` with `LLM_BASE_URL` | Configurable | DeepSeek, Groq, OpenRouter |

### Reasoning Block (`<think>`) Streaming Filter
Modern reasoning models (such as DeepSeek-R1 or Qwen-QwQ) emit internal reasoning inside `<think>...</think>` tags. Jarvis implements a stateful streaming filter (`ThinkingFilter`) that intercepts thinking tokens in flight, preventing internal chain-of-thought scratchpads from leaking into the user-facing chat bubble.

---

## 10. Dual Vector Store Tiers: ChromaDB & Pinecone

### A. Local ChromaDB Tier
- Stores document chunks and dense embeddings on disk at `./backend/chroma_db`.
- SQLite-backed persistence requiring zero cloud credentials or network access.

### B. Serverless Pinecone Cloud Tier (`backend/core/vectorstore.py`)
- Enabled via `VECTOR_BACKEND=pinecone`.
- **Dynamic Index Creation**: Probes the dimension of the active embedding model (768 for Gemini, 1024 for Ollama, 1536 for OpenAI) and automatically provisions the Pinecone serverless index if it does not exist.
- **Dimension Validation**: Checks existing index dimensions and raises clear error messages if an embedding dimension mismatch is detected.
- **Full Spread Support**: Implements document filtering and chunk sorting over Pinecone metadata, ensuring document summaries work seamlessly in hosted mode.

---

## 11. Bidirectional Push-to-Talk Voice Pipeline

1. **Audio Capture**: Browser `MediaRecorder` captures microphone audio in `audio/webm` format while the user holds the microphone button.
2. **Audio Streaming**: On button release, the audio blob is posted to `/api/voice/transcribe`.
3. **Backend Speech-to-Text (`faster-whisper`)**:
   - Transcribes audio on CPU using INT8 quantization (`base.en` or `small.en`).
   - Requires zero GPU VRAM.
   - **Lazy Loading**: When `STT_ENABLED=false` (e.g. low-memory cloud hosts), PyAV, Torch audio, and Whisper modules are never imported, saving ~500MB of RAM.
4. **Backend Speech Synthesis (`edge-tts`)**:
   - The assistant answer is synthesized into natural neural speech using Microsoft Edge-TTS (`en-US-AriaNeural` or `en-US-GuyNeural`).
   - Returns an `audio/mpeg` stream played directly in the browser via Web Audio API.

---

## 12. Server-Sent Events (SSE) Streaming Protocol

The `/api/chat` route streams structured lifecycle events over `text/event-stream`:

```
event: status
data: {"status": "searching", "message": "Searching the web..."}

event: sources
data: {
  "type": "sources",
  "source_type": "web",
  "path": "web",
  "fallback_reason": "low_similarity",
  "best_score": 0.22,
  "sources": [
    {"title": "Page Title", "url": "https://example.com", "snippet": "..."}
  ]
}

event: token
data: {"token": "The "}

event: done
data: {"status": "complete"}
```

---

## 13. Security, Rate Limiting & Proxy Compatibility

1. **Proxy-Aware Rate Limiting**:
   - Inspects `X-Forwarded-For` and extracts the first (client) IP address when deployed behind Cloudflare, Nginx, or AWS ALB.
   - Falls back to `client.host` in direct local connections.
2. **Upload Protections**:
   - Enforces `MAX_UPLOAD_MB` (default 25 MB) to prevent denial-of-service via large file uploads.
3. **SSE Proxy Buffering Notice**:
   - Emits `X-Accel-Buffering: no` on all streaming routes to instruct reverse proxies not to buffer SSE tokens.

---

## 14. Deployment: Local & Cloud Topologies

### Topology A: 100% Local Deployment (Default)
- **FastAPI Backend**: `http://127.0.0.1:8000`
- **Vite Frontend**: `http://127.0.0.1:5173`
- **Ollama Engine**: `http://127.0.0.1:11434`
- **Storage**: Local ChromaDB on disk

### Topology B: Serverless Cloud Deployment
- **Backend**: Hosted on Render, Railway, Fly.io, or AWS using `uvicorn main:app --host 0.0.0.0 --port 8000`.
- **Frontend**: Hosted on Vercel, Netlify, or Cloudflare Pages with `VITE_API_BASE_URL=https://your-backend.onrender.com`.
- **Inference**: Google Gemini (`LLM_PROVIDER=gemini`) or OpenAI (`LLM_PROVIDER=openai`).
- **Vectors**: Pinecone Serverless (`VECTOR_BACKEND=pinecone`).
- **Voice**: `STT_ENABLED=false` for lightweight serverless execution.

---

## 15. Automated Scripts (setup.bat, start_all.bat, stop_all.bat)

To enable a zero-configuration developer experience on Windows:
1. **`setup.bat`**:
   - Validates Python and Node.js installations.
   - Automatically provisions `backend/.venv`.
   - Copies `.env.example` to `backend/.env`.
   - Installs all backend requirements via `pip install -r requirements.txt`.
   - Installs all frontend packages via `npm install`.
2. **`start_all.bat`**:
   - Verifies the virtual environment and `.env`.
   - Spawns Ollama (`ollama serve`), FastAPI (`uvicorn`), and Vite (`npm run dev`) into three dedicated terminal windows.
3. **`stop_all.bat`**:
   - Gracefully shuts down Ollama, Uvicorn, and Node dev server processes.

---

## 16. Verification History & Resolved Challenges

| Challenge Encountered | Root Cause | Technical Resolution |
| :--- | :--- | :--- |
| **Search snippet truncation** | DuckDuckGo snippets truncate at ~150 chars, cutting off dates buried in forum threads. | Broadened query terms, cleaned forum headers, and allowed multi-source synthesis. |
| **Mechanical fallback repetitions** | Hardcoded prompt instructing the LLM to output rigid fallback strings. | Rewrote search system prompts to summarize best available context and temporal anchors. |
| **System clock missing regex matches** | Previous regex checked only exact `"today's date"` phrases. | Broadened date regex patterns and handled clock queries directly from `datetime.now()`. |
| **Sub-version over-anchoring** | Multi-turn reformulator anchored to patch numbers rather than root game titles. | Updated pronoun reformulation prompt to resolve root entities and ignore patch versions. |
| **Whisper import overhead in cloud** | `faster-whisper` imported PyAV and Torch at module startup even when voice was disabled. | Implemented lazy loading for STT; when `STT_ENABLED=false`, heavy libraries are never loaded. |
| **Pinecone dimension mismatch** | In hosted mode, user embedding model dimension differed from existing Pinecone index. | Implemented auto-detection of model dimension, automated index provisioning, and clear validation errors. |
| **Emoji standard enforcement** | Project documentation contained decorative emojis that conflicted with professional standards. | Stripped all decorative symbols across `README.md`, backend responses, and frontend error notices. |

---

*Documentation compiled and verified for Jarvis v1.0.0 (Master Branch).*
