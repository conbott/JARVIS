# 🚀 Local RAG & Voice Assistant with Cloud Sync & Web Fallback

An enterprise-grade, full-stack AI Assistant built with **FastAPI**, **React 19 (Vite + Tailwind CSS)**, local GPU acceleration via **Ollama (`qwen2.5-coder:7b` + `qwen3-embedding:0.6b`)**, dual vector database support (**Local ChromaDB** + **Cloud Pinecone Sync**), autonomous **DuckDuckGo Web Search**, and zero-VRAM neural **Voice Synthesis (Edge-TTS)**.

---

## 🌟 Architecture Overview

```
                                      ┌─────────────────────────────────────────────────────────┐
                                      │              FRONTEND (React 19 + Vite)                 │
                                      │  - Real-time Server-Sent Events (SSE) Streaming         │
                                      │  - Drag & Drop Document Ingestion (PDF / TXT / MD)      │
                                      │  - Push-to-Talk Voice Input (Speech Recognition)        │
                                      │  - Natural Audio Playback (Voice In -> Voice Out)       │
                                      │  - One-Click Pinecone Cloud Vector Sync Button          │
                                      └────────────────────────────┬────────────────────────────┘
                                                                   │ Proxy (Port 5173 -> 8000)
                                                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND (FastAPI / Python)                                  │
│                                                                                               │
│  /api/chat (SSE Stream)   /api/documents/upload    /api/documents/sync-pinecone  /api/voice   │
│                                                                                               │
│                     ┌───────────────────────────────────────────────────┐                     │
│                     │             Intelligent RAG Router                │                     │
│                     └───────┬───────────────────────────┬───────────────┘                     │
│                             │                           │                                     │
│                     (Relevant Chunks)           (Below Threshold / Live)                      │
│                             ▼                           ▼                                     │
│                     ┌───────────────┐           ┌───────────────────────┐                     │
│                     │ Local Chroma  │           │ DuckDuckGo Live Web   │                     │
│                     │  Vector Store │           │    Search Fallback    │                     │
│                     └───────┬───────┘           └───────────┬───────────┘                     │
│                             │                               │                                 │
│                             └───────────────┬───────────────┘                                 │
│                                             ▼                                                 │
│                               ┌───────────────────────────┐                                   │
│                               │ Ollama Local GPU Engine   │                                   │
│                               │ - qwen2.5-coder:7b        │                                   │
│                               │ - 100% in 6 GB VRAM       │                                   │
│                               └───────────────────────────┘                                   │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons | Dark mode, token streaming, code block copy, push-to-talk mic |
| **Backend** | FastAPI, Uvicorn, Pydantic v2, Python 3.11+ | Asynchronous REST + Server-Sent Events (SSE) |
| **Core LLM** | `qwen2.5-coder:7b` | Runs 100% on NVIDIA GPU (~4.7 GB VRAM) at ~35-45 tok/s |
| **Embeddings** | `qwen3-embedding:0.6b` | Fast, high-dimensional vector embeddings on GPU (~600 MB VRAM) |
| **Local Vector DB** | ChromaDB | Offline, persistent vector storage on local disk |
| **Cloud Vector DB** | Pinecone | On-demand synchronization to free cloud index (`attention-paper`) |
| **Live Web Search** | DuckDuckGo (`ddgs`) | Autonomous fallback when documents lack context (100% free, zero API key) |
| **Voice Engine** | Edge-TTS + Web Speech API | Natural Microsoft Neural voices (`en-US-GuyNeural`) running on CPU |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Ollama** installed with models pulled:
  ```powershell
  ollama pull qwen2.5-coder:7b
  ollama pull qwen3-embedding:0.6b
  ollama serve
  ```

### 2. Start Backend Server
```powershell
cd backend
# Create virtual environment if not already created
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

### 3. Start Frontend Development Server
```powershell
cd frontend
npm install
npm run dev
```
Open **[http://127.0.0.1:5173](http://127.0.0.1:5173)** in your browser!

---

## 🎯 Key Architectural Rules

1. **Two-Stage Storage:**
   - Ingest PDFs or text files through the UI drawer. They are automatically chunked, embedded via `qwen3-embedding:0.6b`, and stored in **ChromaDB**.
   - When ready, click **Sync to Pinecone** in the drawer to push local vectors to your cloud index.
2. **Context-Aware Voice:**
   - **Spoken Input:** Clicking the microphone button triggers voice transcription and automatically speaks the answer back using neural audio synthesis.
   - **Typed Input:** Typing a prompt responds with silent token-by-token streaming text.
3. **Autonomous Web Search:**
   - If document similarity falls below threshold, or if querying recent/live events, the pipeline autonomously executes a DuckDuckGo search, cites the web sources, and synthesizes the answer.

---

## 🌐 Deployment Guidelines

- **Frontend (Static / SPA):** Can be deployed in seconds to **Vercel**, **Netlify**, or **Cloudflare Pages** by connecting your GitHub repo and running `npm run build` with output directory `dist`.
- **Backend (API / LLM):** 
  - To keep 100% free local inference on your laptop, run the backend locally or expose via `ngrok` / `Cloudflare Tunnel`.
  - Alternatively, deploy the FastAPI container to **Render**, **Fly.io**, or **Railway** with cloud model fallback or cloud Ollama endpoints.
