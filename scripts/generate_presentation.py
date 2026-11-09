import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="docs/Jarvis_Presentation.pptx"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    # Theme colors
    bg_color = RGBColor(18, 24, 19)        # #121813 Deep Forest Black
    card_color = RGBColor(26, 34, 27)      # #1a221b Forest Moss
    accent_green = RGBColor(168, 213, 162) # #a8d5a2 Sage Green
    accent_cyan = RGBColor(56, 189, 248)   # #38bdf8 Sky Blue
    accent_yellow = RGBColor(251, 191, 36) # #fbbf24 Amber
    text_white = RGBColor(248, 250, 252)   # #f8fafc
    text_muted = RGBColor(148, 163, 184)   # #94a3b8
    border_color = RGBColor(46, 59, 48)    # #2e3b30

    def set_slide_background(slide):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = bg_color
        return shape

    def add_header(slide, title_text, category_text="JARVIS RAG & VOICE ASSISTANT"):
        # Category Tracker
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = "Arial"
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = accent_green

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = "Arial"
        p_title.font.size = Pt(22)
        p_title.font.bold = True
        p_title.font.color.rgb = text_white

    def add_card(slide, left, top, width, height, title, items, title_color=accent_green):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = card_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)

        tx_box = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), height - Inches(0.3))
        tf = tx_box.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.name = "Arial"
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = title_color
        p_t.space_after = Pt(8)

        for item in items:
            p = tf.add_paragraph()
            p.text = "• " + item
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.color.rgb = text_white
            p.space_after = Pt(5)

    # ==========================================
    # SLIDE 1: Title Slide
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(11.3), Inches(3.0))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "JARVIS: LOCAL RAG & VOICE ASSISTANT"
    p0.font.name = "Arial"
    p0.font.size = Pt(32)
    p0.font.bold = True
    p0.font.color.rgb = accent_green
    p0.space_after = Pt(12)

    p1 = tf1.add_paragraph()
    p1.text = "Private, Offline-Capable Full-Stack RAG Architecture, Spread Retrieval & Voice Pipeline"
    p1.font.name = "Arial"
    p1.font.size = Pt(16)
    p1.font.color.rgb = text_white
    p1.space_after = Pt(28)

    p2 = tf1.add_paragraph()
    p2.text = "Engineering Project Defense & Presentation | November 2026 | Repository: github.com/conbott/JARVIS"
    p2.font.name = "Arial"
    p2.font.size = Pt(12)
    p2.font.color.rgb = text_muted

    # ==========================================
    # SLIDE 2: Problem Statement & Core Motivation
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Problem Statement & Project Motivation", "THE MOTIVATION")

    add_card(s2, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1), 
             "Common RAG Pitfalls", [
                 "Cloud LLM API Costs: Subscription and token fees scale unsustainably.",
                 "Privacy & Data Leakage: Proprietary documents sent to external servers.",
                 "Retrieval Tunnel Vision: Passing irrelevant context when documents don't have the answer.",
                 "Top-k Summary Failure: Standard top-k clusters around 1 section and misses the rest of the paper.",
                 "Date & Time Hallucinations: Models output static training dates or brackets."
             ], accent_cyan)

    add_card(s2, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.1), 
             "The Jarvis Solution", [
                 "100% Offline Local Operation: Ollama (Qwen2.5-Coder 7B) + ChromaDB SQLite.",
                 "Dual-Tier Cloud Scalability: Seamless switch to Gemini/Pinecone without code changes.",
                 "Dynamic Similarity Routing: Checks cosine similarity against tau = 0.35 with web search fallback.",
                 "Spread Retrieval: Guarantees Abstract + Conclusion + Strided Page Sampling.",
                 "Zero-GPU Voice Pipeline: Faster-Whisper INT8 on CPU + Edge-TTS streaming."
             ], accent_green)

    # ==========================================
    # SLIDE 3: System Architecture & Workflow
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Full-Stack System Architecture", "SYSTEM ARCHITECTURE")

    add_card(s3, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Decoupled Architectural Layers", [
                 "Frontend: React 19 + TypeScript + Tailwind CSS v4 in nature-green dark palette.",
                 "API Gateway: FastAPI ASGI server with async SSE streaming & proxy rate-limiting.",
                 "Core Engine (backend/core): rag_chain.py routes between documents, web search, and clock.",
                 "Vector Store: ChromaDB SQLite on disk with 1024-dim dense embeddings.",
                 "Speech Subsystem: Faster-Whisper (CPU speech-to-text) + Microsoft Edge-TTS."
             ], accent_green)

    if os.path.exists("docs/screenshots/chat_interface.png"):
        s3.shapes.add_picture("docs/screenshots/chat_interface.png", Inches(6.8), Inches(1.7), width=Inches(5.7))

    # ==========================================
    # SLIDE 4: Document Ingestion & Chunking
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Document Ingestion & Chunking Strategy", "DATA PREPROCESSING")

    add_card(s4, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Chunking: Recursive Character Splitter", [
                 "Chunk Size: 800 characters | Chunk Overlap: 150 characters.",
                 "Separator Priority: '\\n\\n' -> '\\n' -> '. ' -> ' ' -> ''.",
                 "Paragraph & Sentence Integrity: Cuts along natural sentence boundaries rather than mid-word.",
                 "Metadata Preservation: 1-based page numbers, filenames, and timestamps persisted into vectors.",
                 "Payload Protection: 25 MB max upload limit enforced at gateway."
             ], accent_cyan)

    add_card(s4, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Why Not Other Chunking Methods?", [
                 "Naïve Character Chunking: Slices text at rigid character count, splitting words in half ('mach-' ... '-ine').",
                 "Pure Sentence Chunking: Produces erratic chunk sizes (from 20-char fragments to 2000-char paragraphs).",
                 "Recursive Character Chunking (Jarvis): Bounded maximum character budget with semantic punctuation preservation.",
                 "Storage: Persisted into local SQLite database at backend/chroma_db/chroma.sqlite3."
             ], accent_yellow)

    # ==========================================
    # SLIDE 5: The Spread Retrieval Algorithm
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "The Spread Retrieval Algorithm for Summaries", "RETRIEVAL ALGORITHMS")

    add_card(s5, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Why Standard Top-k Similarity Fails", [
                 "When a user asks: 'Summarize this paper' or 'What are the key findings?', summary semantics are distributed across 10-20 pages.",
                 "Top-k similarity clusters around one dense section (e.g. 4 chunks from Section 2).",
                 "It completely misses the introduction, methodology, and conclusions.",
                 "Result: Incomplete, biased summaries that hallucinate missing sections."
             ], accent_yellow)

    add_card(s5, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "The 5-Stage Spread Retrieval Pipeline", [
                 "1. Citation Filtering: Regex drops bibliography chunks ('References', '[1]', 'arXiv:').",
                 "2. Abstract Anchoring: Guarantees inclusion of Chunk 0 (introduction / hypothesis).",
                 "3. Conclusion Anchoring: Guarantees inclusion of Chunk -1 (experimental takeaways).",
                 "4. Uniform Strided Sampling: Calculates stride across middle pages to sample intermediate sections evenly.",
                 "5. SSE Tagging: Emits retrieval='spread' for clean UI badges without misleading point scores."
             ], accent_green)

    # ==========================================
    # SLIDE 6: Dynamic Similarity Routing & Web Fallback
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Cosine Similarity Routing & Live Web Fallback", "DECISION ENGINE")

    add_card(s6, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Similarity Threshold Formulation", [
                 "Mathematical Conversion: ChromaDB cosine distance D in [0, 2] converted to Similarity S = 1.0 - D.",
                 "Routing Threshold tau = 0.35: Empirically separates relevant matches from out-of-domain noise.",
                 "Score >= 0.35: Grounded document answer citing filename and page number.",
                 "Score < 0.35: Automatically falls back to real-time DuckDuckGo web search.",
                 "Multi-Turn Pronoun Reformulation: Rewrites queries like 'when was it released?' into standalone entity searches."
             ], accent_cyan)

    if os.path.exists("docs/charts/cosine_similarity_distribution.png"):
        s6.shapes.add_picture("docs/charts/cosine_similarity_distribution.png", Inches(6.8), Inches(1.7), width=Inches(5.7))

    # ==========================================
    # SLIDE 7: Voice Pipeline: Zero GPU VRAM
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Bidirectional Push-to-Talk Voice Pipeline", "VOICE SUBSYSTEM")

    add_card(s7, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Zero GPU VRAM Voice Architecture", [
                 "Client Audio: Browser MediaRecorder captures audio/webm on microphone hold.",
                 "Faster-Whisper (STT): Transcribes audio on CPU using INT8 quantization in ~380 ms.",
                 "Why CPU for Voice? Leaves all 6-8 GB GPU VRAM dedicated to the 7B LLM, preventing CUDA OOM crashes.",
                 "Edge-TTS (TTS): Microsoft neural text-to-speech stream with 0 MB GPU overhead.",
                 "Speech Text Cleaner: Strips markdown symbols, code blocks, and URLs before synthesis.",
                 "Total Turnaround: 990 ms sub-second audio response."
             ], accent_green)

    if os.path.exists("docs/charts/voice_pipeline_waterfall.png"):
        s7.shapes.add_picture("docs/charts/voice_pipeline_waterfall.png", Inches(6.8), Inches(1.7), width=Inches(5.7))

    # ==========================================
    # SLIDE 8: Developer Automation & Batch Scripts
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Developer Experience & Batch Automation", "ORCHESTRATION")

    add_card(s8, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "One-Click Automation Scripts", [
                 "setup.bat: Automated Environment Provisioner",
                 "  • Validates Python & Node.js prerequisites.",
                 "  • Provisions backend/.venv & copies .env.example.",
                 "  • Installs pip packages & runs npm install.",
                 "start_all.bat: Concurrent Process Launcher",
                 "  • Launches Ollama (:11434), FastAPI (:8000), and Vite (:5173) in 3 terminals.",
                 "stop_all.bat: Graceful Shutdown",
                 "  • Terminates processes on ports 8000, 5173, and 11434 cleanly."
             ], accent_cyan)

    if os.path.exists("docs/screenshots/github_structure.png"):
        s8.shapes.add_picture("docs/screenshots/github_structure.png", Inches(6.8), Inches(1.7), width=Inches(5.7))

    # ==========================================
    # SLIDE 9: Engineering Post-Mortem & Challenges
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Engineering Post-Mortem: Real Challenges Solved", "VERIFICATION")

    add_card(s9, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Technical Challenges Encountered", [
                 "LLM Date Hallucinations: Model outputted [insert today's date] or calculated relative time wrong.",
                 "Pronoun Ambiguity: Searching 'when was it released?' returned garbage on DuckDuckGo.",
                 "Reasoning Tag Leaks: Reasoning models leaked internal <think>...</think> scratchpads to UI.",
                 "SSE Buffering: Reverse proxies buffered streaming chunks, ruining typing animation."
             ], accent_yellow)

    add_card(s9, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Verified Engineering Solutions", [
                 "System Clock Fast-Path: Regex catches date/time queries and answers from datetime.now() (<50ms).",
                 "Conversational Reformulator: Target LLM prompt resolves pronouns using last 4 chat turns.",
                 "Streaming ThinkingFilter: Stateful buffer discards reasoning tokens before yielding to client.",
                 "Buffer Headers: Emitted X-Accel-Buffering: no & Cache-Control: no-cache on all SSE routes."
             ], accent_green)

    # ==========================================
    # SLIDE 10: Performance Benchmarks & Hardware Scaling
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Experimental Results & Latency Benchmarks", "EVALUATION")

    add_card(s10, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "End-to-End Latency by Routing Path", [
                 "Direct System Clock: 45 ms TTFT | 110 ms Total turnaround.",
                 "Casual Conversation: 120 ms TTFT | 400 ms Total turnaround.",
                 "Document Similarity (top-4): 180 ms TTFT | 560 ms Total turnaround.",
                 "Document Spread Retrieval: 240 ms TTFT | 760 ms Total turnaround.",
                 "DuckDuckGo Live Search: 420 ms TTFT | 910 ms Total turnaround.",
                 "Hybrid Fallback (Doc -> Web): 610 ms TTFT | 1,290 ms Total turnaround."
             ], accent_cyan)

    if os.path.exists("docs/charts/latency_breakdown.png"):
        s10.shapes.add_picture("docs/charts/latency_breakdown.png", Inches(6.8), Inches(1.7), width=Inches(5.7))

    # ==========================================
    # SLIDE 11: Top 5 Likely Examiner Questions
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "Viva Defense: Top 5 Examiner Questions", "VIVA PREPARATION")

    add_card(s11, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Likely Questions (1 - 3)", [
                 "Q1: Why FastAPI instead of Flask? -> Native async streaming, SSE generators, and high-concurrency non-blocking I/O.",
                 "Q2: Why ChromaDB instead of FAISS? -> Built-in SQLite persistence on disk (backend/chroma_db) with document metadata filtering.",
                 "Q3: Why not pure sentence chunking? -> Sentence lengths vary wildly from 20 to 2000 chars; recursive character chunking enforces an 800-char budget while respecting sentence boundaries."
             ], accent_cyan)

    add_card(s11, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Likely Questions (4 - 5)", [
                 "Q4: How do you prevent hallucinations when documents don't have the answer? -> We calculate cosine similarity (S = 1 - D); if best S < 0.35, we trigger DuckDuckGo live search fallback instead of guessing.",
                 "Q5: Why run Faster-Whisper on CPU? -> It consumes 0 MB GPU VRAM via INT8 quantization, leaving all 6-8 GB VRAM dedicated to the 7B LLM to prevent CUDA OOM crashes."
             ], accent_green)

    # ==========================================
    # SLIDE 12: Conclusion & Future Roadmap
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "Conclusion & Future Roadmap", "CONCLUSION")

    add_card(s12, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Key Achievements", [
                 "100% Zero-Cost Local Operation with zero telemetry and private on-disk vectors.",
                 "Novel Spread Retrieval algorithm solving multi-page document summarization.",
                 "Sub-second voice turnaround (990 ms) on consumer workstation hardware.",
                 "Automated single-click Windows deployment and verified multi-provider cloud scaling."
             ], accent_green)

    add_card(s12, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.1),
             "Future Engineering Roadmap", [
                 "Multimodal OCR: Ingest scanned tables & charts via Llama 3.2 Vision.",
                 "Cross-Encoder Reranking: Deploy bge-reranker-large for fine-grained top-k ordering.",
                 "Hybrid Sparse-Dense Search: Combine BM25 keyword frequency with dense Qwen vectors.",
                 "Graph Memory: Long-term episodic conversational memory with graph databases."
             ], accent_cyan)

    prs.save(output_path)
    print(f"Presentation successfully compiled: {output_path}")

if __name__ == '__main__':
    create_deck()
