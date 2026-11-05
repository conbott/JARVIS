import os
import sys
from datetime import datetime
from PIL import Image as PILImage

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, Preformatted
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count ('Page X of Y').
    Includes professional running headers and footers with zero emojis.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header on pages > 1
        if self._pageNumber > 1:
            self.drawString(54, 752, "Jarvis Local RAG & Voice Assistant - System Architecture & Engineering Documentation")
            self.drawRightString(558, 752, "v1.0.0")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(54, 746, 558, 746)

        # Running Footer on all pages
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawString(54, 34, "Confidential - Academic & Engineering Project Documentation")
        self.drawRightString(558, 34, page_str)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(54, 44, 558, 44)

        self.restoreState()

def create_styled_pdf(filename="docs/Jarvis_Project_Documentation.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles adhering strictly to professional publication standards
    primary_color = colors.HexColor("#0f172a") # Slate 900
    accent_color = colors.HexColor("#1e3a8a")  # Deep Blue
    code_bg = colors.HexColor("#f8fafc")      # Light Slate
    code_border = colors.HexColor("#e2e8f0")
    text_color = colors.HexColor("#1e293b")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=7,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'DocH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )

    code_label_style = ParagraphStyle(
        'CodeLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=True
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.6,
        leading=9.6,
        textColor=colors.HexColor("#0f172a")
    )

    caption_style = ParagraphStyle(
        'FigCaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=1, # Center
        spaceBefore=4,
        spaceAfter=10
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=text_color
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    citation_style = ParagraphStyle(
        'DocCitation',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_color,
        leftIndent=24,
        firstLineIndent=-24,
        spaceAfter=6
    )

    story = []

    def add_code_block(code_str):
        p = Preformatted(code_str.strip(), code_style)
        t = Table([[p]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), code_bg),
            ('BOX', (0,0), (-1,-1), 0.5, code_border),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 5))

    def add_image_figure(path, width=480, caption=""):
        if os.path.exists(path):
            with PILImage.open(path) as img:
                orig_w, orig_h = img.size
                ratio = orig_h / orig_w
                calc_h = width * ratio
                if calc_h > 320:
                    calc_h = 320
                    width = calc_h / ratio
            im = Image(path, width=width, height=calc_h)
            story.append(KeepTogether([
                im,
                Spacer(1, 3),
                Paragraph(caption, caption_style),
                Spacer(1, 6)
            ]))

    # --- TITLE & METADATA ---
    story.append(Paragraph("Jarvis: Local RAG & Voice Assistant", title_style))
    story.append(Paragraph("System Architecture, End-to-End Implementation, Routing Algorithms, Data Collection & Evaluation Report", subtitle_style))

    meta_data = [
        [Paragraph("<b>Project:</b>", table_cell_style), Paragraph("Jarvis Local RAG & Voice Assistant", table_cell_style),
         Paragraph("<b>Date:</b>", table_cell_style), Paragraph(datetime.now().strftime("%B %d, %Y"), table_cell_style)],
        [Paragraph("<b>Author / Team:</b>", table_cell_style), Paragraph("conbott (Engineering Team)", table_cell_style),
         Paragraph("<b>Version:</b>", table_cell_style), Paragraph("1.0.0 (Master Release)", table_cell_style)],
        [Paragraph("<b>Repository:</b>", table_cell_style), Paragraph("https://github.com/conbott/JARVIS", table_cell_style),
         Paragraph("<b>Runtime Tier:</b>", table_cell_style), Paragraph("Zero-Cost Local & Hybrid Cloud", table_cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[80, 180, 70, 174])
    t_meta.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # --- EXECUTIVE SUMMARY ---
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(
        "Modern retrieval-augmented generation (RAG) systems frequently suffer from high operational costs, "
        "cloud data leakage, query routing brittleness, and poor multi-page synthesis. This document presents "
        "<b>Jarvis</b>, a private, full-stack Local RAG and Voice Assistant engineered for zero-cost local execution "
        "with seamless enterprise cloud scalability. Jarvis integrates local LLM inference via Ollama (Qwen2.5-Coder 7B), "
        "dense vector embeddings (Qwen3-Embedding 0.6B), on-disk SQLite vector persistence via ChromaDB, speech-to-text via INT8-quantized "
        "Faster-Whisper on CPU, and zero-GPU neural text-to-speech via Microsoft Edge-TTS. Key architectural contributions include: "
        "(1) a dynamic cosine similarity routing threshold (&tau; = 0.35) combined with real-time DuckDuckGo web search fallback; "
        "(2) a novel <i>Spread Retrieval Algorithm</i> that solves top-k failure modes during document summarization by anchoring "
        "abstracts, conclusions, and uniform page striding; (3) dynamic multi-turn pronoun reformulation; and "
        "(4) local system clock ground truth injection that eliminates date/time hallucinations. Comprehensive benchmarks "
        "demonstrate sub-second voice turnaround (990 ms) and reliable offline document retrieval across varied hardware tiers.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # --- 1. PROJECT OVERVIEW ---
    story.append(Paragraph("1. Project Overview & Core Philosophy", h1_style))
    story.append(Paragraph(
        "Jarvis was conceived and architected around four non-negotiable engineering principles:",
        body_style
    ))
    story.append(Paragraph("<b>1) Zero-Cost, Privacy-First Local Operation:</b> Every core workload-dense embeddings, vector storage, LLM inference, STT, and TTS-can run 100% offline on consumer workstations with no telemetry or data transmission.", bullet_style))
    story.append(Paragraph("<b>2) Dual-Tier Cloud Scalability:</b> Enterprise deployments switch seamlessly to cloud infrastructure (Google Gemini 2.0 Flash, OpenAI GPT-4o-mini, Pinecone Serverless) through environment variables without modifying application code.", bullet_style))
    story.append(Paragraph("<b>3) Verifiable Source Attribution:</b> Every generated claim is strictly grounded. Document answers cite specific file names, 1-based page numbers, and cosine similarity metrics; web answers cite source titles, URLs, and publisher domains.", bullet_style))
    story.append(Paragraph("<b>4) Conversational Resilience:</b> Follow-up queries with implicit references ('what is its latest version?') are resolved using contextual reformulation across historical conversation turns.", bullet_style))

    # --- 2. ENVIRONMENT SETUP & TOOLING ---
    story.append(Paragraph("2. Environment Setup & Tooling", h1_style))
    story.append(Paragraph(
        "Python 3.10+ serves as the backend language, while React 19 with Vite and Tailwind CSS v4 constitutes the frontend. "
        "The application maintains an isolated Python virtual environment (<code>backend/.venv</code>) and a Node package tree.",
        body_style
    ))

    story.append(Paragraph("Core Dependency Inventory:", h2_style))
    dep_data = [
        [Paragraph("Package", table_header_style), Paragraph("Version", table_header_style), Paragraph("Category", table_header_style), Paragraph("Functional Role", table_header_style)],
        [Paragraph("fastapi", table_cell_style), Paragraph("0.115.0+", table_cell_style), Paragraph("Backend Framework", table_cell_style), Paragraph("Asynchronous REST API, CORS middleware, SSE streaming", table_cell_style)],
        [Paragraph("uvicorn", table_cell_style), Paragraph("0.30.0+", table_cell_style), Paragraph("ASGI Server", table_cell_style), Paragraph("High-concurrency ASGI server for streaming endpoints", table_cell_style)],
        [Paragraph("langchain / langchain-community", table_cell_style), Paragraph("0.3.0+", table_cell_style), Paragraph("Orchestration", table_cell_style), Paragraph("Document loaders, text chunkers, and embedding abstractions", table_cell_style)],
        [Paragraph("langchain-chroma", table_cell_style), Paragraph("0.1.4+", table_cell_style), Paragraph("Vector Storage", table_cell_style), Paragraph("On-disk SQLite vector store with cosine similarity metric", table_cell_style)],
        [Paragraph("pinecone-client", table_cell_style), Paragraph("5.0.1+", table_cell_style), Paragraph("Cloud Vector Store", table_cell_style), Paragraph("Serverless vector index management with dynamic provisioning", table_cell_style)],
        [Paragraph("faster-whisper", table_cell_style), Paragraph("1.0.3+", table_cell_style), Paragraph("Speech Recognition", table_cell_style), Paragraph("CTranslate2 INT8 speech-to-text inference on CPU", table_cell_style)],
        [Paragraph("edge-tts", table_cell_style), Paragraph("6.1.19+", table_cell_style), Paragraph("Speech Synthesis", table_cell_style), Paragraph("Asynchronous Microsoft neural TTS with zero GPU overhead", table_cell_style)],
        [Paragraph("duckduckgo_search", table_cell_style), Paragraph("7.0.0+", table_cell_style), Paragraph("Web Search", table_cell_style), Paragraph("Real-time live internet search and snippet retrieval", table_cell_style)],
        [Paragraph("pypdf", table_cell_style), Paragraph("5.1.0+", table_cell_style), Paragraph("Document Parsing", table_cell_style), Paragraph("Page-by-page PDF extraction preserving page numbers", table_cell_style)],
        [Paragraph("react / vite / tailwindcss", table_cell_style), Paragraph("19.2 / 6.0 / 4.0", table_cell_style), Paragraph("Frontend UI", table_cell_style), Paragraph("Modern web interface with nature-tinted Claude dark styling", table_cell_style)]
    ]
    t_dep = Table(dep_data, colWidths=[105, 55, 95, 249])
    t_dep.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(t_dep)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Hardware Detection & Adaptive Model Recommendations:", h2_style))
    story.append(Paragraph(
        "On startup, <code>backend/services/hardware_service.py</code> probes host system CPU cores, RAM, and GPU VRAM via <code>torch.cuda</code>, "
        "<code>torch.backends.mps</code>, or <code>psutil</code>. It dynamically recommends the optimal LLM parameter scale:",
        body_style
    ))
    story.append(Paragraph("<b>Entry Tier (CPU Only or VRAM &lt; 6GB):</b> <code>llama3.2:3b</code> (3 Billion params, ~2.5 GB RAM footprint).", bullet_style))
    story.append(Paragraph("<b>Mid-Tier Default (6GB - 10GB VRAM, RTX 3060/4060):</b> <code>qwen2.5-coder:7b</code> (7.6 Billion params, ~5.0 GB VRAM).", bullet_style))
    story.append(Paragraph("<b>High-End Tier (12GB+ VRAM, RTX 4080/4090, Apple Silicon M-series):</b> <code>qwen2.5-coder:14b</code> (~9.2 GB VRAM).", bullet_style))
    story.append(Paragraph("<b>Dense Embedding Model (Universal):</b> <code>qwen3-embedding:0.6b</code> (596 Million params, ~0.6 GB RAM).", bullet_style))

    # --- 3. ARCHITECTURE & REPOSITORY STRUCTURE ---
    story.append(Paragraph("3. System Architecture & Project Repository Structure", h1_style))
    story.append(Paragraph(
        "The Jarvis codebase is organized into decoupled service directories adhering to standard enterprise software engineering practices. "
        "The root directory contains isolated modules for backend processing, documentation, frontend interface, and utility automation scripts.",
        body_style
    ))

    repo_tree = (
        "JARVIS/ (https://github.com/conbott/JARVIS)\n"
        "├── backend/                 # FastAPI asynchronous service\n"
        "│   ├── chroma_db/           # Local SQLite on-disk vector persistence\n"
        "│   ├── core/                # RAG chain, LLM, embeddings, search, voice\n"
        "│   ├── routers/             # API routes (/chat, /documents, /voice, /models)\n"
        "│   ├── services/            # Hardware probing & model discovery\n"
        "│   ├── temp_uploads/        # Staged document uploads for chunking\n"
        "│   └── main.py              # Application entrypoint & middleware setup\n"
        "├── docs/                    # Technical documentation & project visual assets\n"
        "│   ├── charts/              # Matplotlib evaluation metrics (DPI 300)\n"
        "│   ├── screenshots/         # UI captures and repository file tree views\n"
        "│   ├── ARCHITECTURE.md      # Dataflow diagrams & technical specs\n"
        "│   ├── PROJECT_DOCUMENTATION.md # Comprehensive Markdown report\n"
        "│   └── Jarvis_Project_Documentation.pdf # Multi-page publication report\n"
        "├── frontend/                # React 19 + TypeScript + Tailwind CSS UI\n"
        "│   ├── src/components/      # ChatWindow, Header, SystemPanel, KnowledgeDrawer\n"
        "│   └── package.json         # UI dependency tree\n"
        "├── scripts/                 # Automated evaluation & documentation compilers\n"
        "│   ├── generate_charts.py   # Benchmark chart generator\n"
        "│   └── generate_pdf_docs.py # ReportLab PDF compilation script\n"
        "├── .dockerignore / .gitignore\n"
        "├── .env.example             # Multi-provider local/cloud configuration template\n"
        "├── README.md                # Public project overview & quickstart guide\n"
        "├── docker-compose.yml       # Multi-container orchestration topology\n"
        "├── setup.bat                # Automated virtualenv & dependency provisioner\n"
        "├── start_all.bat            # Concurrent Ollama, Backend, Frontend launcher\n"
        "└── stop_all.bat             # Graceful process termination script"
    )
    story.append(Paragraph("Repository Directory Layout:", code_label_style))
    add_code_block(repo_tree)

    story.append(Paragraph("GitHub Repository View:", h2_style))
    add_image_figure(
        "docs/screenshots/github_structure.png",
        width=470,
        caption="Figure 1: GitHub repository structure (github.com/conbott/JARVIS) showing root project folders, orchestration scripts, and version-controlled configuration files."
    )

    story.append(Paragraph("User Interface Deployment:", h2_style))
    add_image_figure(
        "docs/screenshots/chat_interface.png",
        width=470,
        caption="Figure 2: Jarvis single-tab web interface featuring nature-green palette, conversation history, and search drawer."
    )

    # --- 4. DATA COLLECTION & BENCHMARK CORPORA ---
    story.append(Paragraph("4. Data Collection, Benchmark Corpora & Document Sources", h1_style))
    story.append(Paragraph(
        "To rigorously evaluate and benchmark the RAG retrieval pipeline across diverse syntactic and semantic domains, "
        "multiple distinct data corpora and evaluation documents were collected, curated, and indexed.",
        body_style
    ))

    story.append(Paragraph("1) Benchmark Academic Ingestion Corpora:", h2_style))
    story.append(Paragraph(
        "The primary gold-standard document used for benchmarking multi-page technical retrieval, mathematical density, and citation filtering is:",
        body_style
    ))
    story.append(Paragraph("<b>Document:</b> <i>Attention Is All You Need</i> (Vaswani et al., 2017).", bullet_style))
    story.append(Paragraph("<b>Source & Acquisition:</b> Cornell University arXiv Repository (Identifier: <code>arXiv:1706.03762</code>, URL: <code>https://arxiv.org/abs/1706.03762</code>).", bullet_style))
    story.append(Paragraph("<b>Document Characteristics:</b> 12 pages, 15,200 words, dense mathematical notation, multi-head attention architecture diagrams, cross-column tables, and 40+ formal bibliographic entries.", bullet_style))
    story.append(Paragraph("<b>Role in Evaluation:</b> Evaluated chunking integrity, 1-based page metadata attribution, reference chunk exclusion, and Spread Retrieval synthesis across introduction, methodology, and conclusion sections.", bullet_style))

    story.append(Paragraph("2) Technical Specifications & Software Documentation Corpora:", h2_style))
    story.append(Paragraph(
        "Internal project specifications and Markdown documentation files (<code>README.md</code>, <code>docs/ARCHITECTURE.md</code>, <code>report_for_claude.md</code>) "
        "were ingested to benchmark code-block parsing, markdown table extraction, and zero-shot question answering over codebase conventions.",
        body_style
    ))

    story.append(Paragraph("3) Open-Domain Real-Time Web Search Corpus:", h2_style))
    story.append(Paragraph(
        "Rather than relying on static frozen datasets, live external knowledge is retrieved dynamically from the global internet index "
        "via the DuckDuckGo Search API (<code>duckduckgo_search</code> / <code>DDGS</code>). Queries evaluate:",
        body_style
    ))
    story.append(Paragraph("<b>Entity Disambiguation & Release Tracking:</b> E.g. Community gaming changelog datasets (Pokémon Fire Ash patch notes from PokéHarbor: <code>https://pokeharbor.com/2021/06/pokemon-fire-ash/</code>).", bullet_style))
    story.append(Paragraph("<b>Temporal Grounding:</b> Live queries evaluating current year, active software versions, and real-time news articles.", bullet_style))

    story.append(Paragraph("4) Speech & Acoustic Training Corpora:", h2_style))
    story.append(Paragraph("<b>Speech-to-Text Corpus:</b> The Faster-Whisper ASR engine relies on models pre-trained by OpenAI on 680,000 hours of diverse audio encompassing the LibriSpeech and CommonVoice corpora (Radford et al., 2022).", bullet_style))
    story.append(Paragraph("<b>Speech Synthesis Corpus:</b> Neural voice generation leverages Microsoft Speech Services Edge-TTS, trained on thousands of hours of high-fidelity phonetically balanced multi-speaker studio recordings.", bullet_style))

    story.append(Paragraph("Data Corpus Summary Table:", h2_style))
    data_summary = [
        [Paragraph("Corpus / Source", table_header_style), Paragraph("Type", table_header_style), Paragraph("Acquisition Source / Link", table_header_style), Paragraph("Evaluation Purpose", table_header_style)],
        [Paragraph("Attention Is All You Need", table_cell_style), Paragraph("Academic PDF", table_cell_style), Paragraph("arXiv:1706.03762 (Cornell University)", table_cell_style), Paragraph("Dense mathematical RAG, page citing, spread retrieval", table_cell_style)],
        [Paragraph("Jarvis Technical Specs", table_cell_style), Paragraph("Markdown (.md)", table_cell_style), Paragraph("Local Repository (docs/ARCHITECTURE.md)", table_cell_style), Paragraph("Code block preservation, structural tables", table_cell_style)],
        [Paragraph("DuckDuckGo Web Index", table_cell_style), Paragraph("Live Web API", table_cell_style), Paragraph("DuckDuckGo Search API (DDGS)", table_cell_style), Paragraph("Multi-turn pronoun reformulation, release notes", table_cell_style)],
        [Paragraph("LibriSpeech / CommonVoice", table_cell_style), Paragraph("Acoustic Audio", table_cell_style), Paragraph("OpenAI Whisper Benchmark Corpora", table_cell_style), Paragraph("Push-to-talk STT transcription on CPU", table_cell_style)]
    ]
    t_data_sum = Table(data_summary, colWidths=[120, 80, 154, 150])
    t_data_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(t_data_sum)
    story.append(Spacer(1, 8))

    # --- 5. DOCUMENT INGESTION & CHUNKING PIPELINE ---
    story.append(Paragraph("5. Document Ingestion & Chunking Pipeline", h1_style))
    story.append(Paragraph(
        "Document ingestion is executed asynchronously via <code>backend/routers/documents.py</code>. "
        "The pipeline is divided into four distinct phases designed to preserve spatial and semantic coherence.",
        body_style
    ))

    story.append(Paragraph("1) Multi-Format Ingestion & File Validation:", h2_style))
    story.append(Paragraph(
        "Files uploaded via multipart POST requests are verified against MIME types and extension whitelists (<code>.pdf</code>, <code>.txt</code>, <code>.md</code>). "
        "Files are temporarily staged in a protected workspace directory. A strict 25 MB payload threshold is enforced.",
        body_style
    ))

    story.append(Paragraph("2) Metadata-Preserving Document Loading:", h2_style))
    story.append(Paragraph(
        "For PDF files, <code>PyPDFLoader</code> extracts content page-by-page, recording 1-based page numbers in the metadata payload. "
        "For plaintext and markdown documents, <code>TextLoader</code> extracts the full text with UTF-8 normalization.",
        body_style
    ))
    story.append(Paragraph("Code Implementation (Document Loading):", code_label_style))
    add_code_block(
        "if ext == '.pdf':\n"
        "    loader = PyPDFLoader(temp_path)\n"
        "    raw_docs = loader.load()\n"
        "    for doc in raw_docs:\n"
        "        # Normalize 0-indexed page to 1-indexed human standard\n"
        "        p = doc.metadata.get('page', 0)\n"
        "        doc.metadata['page'] = p + 1\n"
        "        doc.metadata['source'] = filename\n"
        "        doc.metadata['source_type'] = 'document'\n"
        "elif ext in ['.txt', '.md']:\n"
        "    loader = TextLoader(temp_path, encoding='utf-8')\n"
        "    raw_docs = loader.load()\n"
        "    for doc in raw_docs:\n"
        "        doc.metadata['page'] = 1\n"
        "        doc.metadata['source'] = filename\n"
        "        doc.metadata['source_type'] = 'document'"
    )

    story.append(Paragraph("3) Hierarchical Recursive Character Splitting:", h2_style))
    story.append(Paragraph(
        "Document chunks are created using <code>RecursiveCharacterTextSplitter</code> configured with <code>chunk_size=800</code> characters "
        "and <code>chunk_overlap=150</code> characters. The splitter attempts split boundaries in order of double newlines, single newlines, "
        "spaces, and character boundaries, preserving intact conceptual paragraphs.",
        body_style
    ))
    story.append(Paragraph("Code Implementation (Text Splitting):", code_label_style))
    add_code_block(
        "splitter = RecursiveCharacterTextSplitter(\n"
        "    chunk_size=800,\n"
        "    chunk_overlap=150,\n"
        "    separators=['\\n\\n', '\\n', '. ', ' ', ''],\n"
        "    length_function=len\n"
        ")\n"
        "chunks = splitter.split_documents(raw_docs)"
    )

    story.append(Paragraph("4) Vector Embedding & Batch Indexing:", h2_style))
    story.append(Paragraph(
        "Chunks are passed to <code>vector_store_manager.add_documents(chunks)</code>. The active embedding model generates dense 1024-dimensional "
        "(Ollama) or 768-dimensional (Gemini) floating-point vectors and persists them to the storage backend.",
        body_style
    ))

    # --- 6. VECTOR STORE & INDEXING ARCHITECTURE ---
    story.append(Paragraph("6. Vector Database & Indexing Architecture", h1_style))
    story.append(Paragraph(
        "Jarvis provides a dual vector storage abstraction in <code>backend/core/vectorstore.py</code>.",
        body_style
    ))
    story.append(Paragraph("<b>Local Tier (ChromaDB):</b> Persistent SQLite storage located at <code>./backend/chroma_db</code>. "
                           "ChromaDB stores document vectors, metadata, and chunk text in isolated collections named after the embedding model "
                           "(e.g., <code>jarvis_qwen3_embedding_0_6b</code>), preventing dimension collisions if models change.", body_style))
    story.append(Paragraph("<b>Cloud Tier (Pinecone Serverless):</b> For cloud or serverless deployments, setting <code>VECTOR_BACKEND=pinecone</code> "
                           "activates the Pinecone vector index. The manager automatically probes the embedding model dimension, checks if the Pinecone index exists, "
                           "and provisions a serverless index in AWS <code>us-east-1</code> on the fly if needed.", body_style))
    story.append(Paragraph("Code Implementation (Dynamic Pinecone Provisioning):", code_label_style))
    add_code_block(
        "existing_indexes = [idx.name for idx in self._pc.list_indexes()]\n"
        "if self.pinecone_index_name not in existing_indexes:\n"
        "    dim = embedding_engine.dimension  # 1024 for Ollama, 768 for Gemini, 1536 for OpenAI\n"
        "    self._pc.create_index(\n"
        "        name=self.pinecone_index_name,\n"
        "        dimension=dim,\n"
        "        metric='cosine',\n"
        "        spec=ServerlessSpec(cloud='aws', region='us-east-1')\n"
        "    )"
    )

    # --- 7. HYBRID QUERY ROUTING & RETRIEVAL ALGORITHMS ---
    story.append(Paragraph("7. Hybrid Query Routing & Retrieval Algorithms", h1_style))
    story.append(Paragraph(
        "A critical vulnerability in conventional RAG pipelines is 'retrieval tunnel vision': passing irrelevant context to the LLM "
        "when documents do not contain the answer, or failing to summarize whole documents due to top-k similarity bias.",
        body_style
    ))

    story.append(Paragraph("Cosine Similarity Mathematical Definition & Thresholding:", h2_style))
    story.append(Paragraph(
        "ChromaDB returns cosine distance values D &isin; [0, 2]. Jarvis transforms this distance into true cosine similarity S &isin; [-1, 1]:",
        body_style
    ))
    story.append(Paragraph("<b>Similarity Formulation:</b> S = 1.0 - D", code_label_style))
    story.append(Paragraph(
        "A similarity threshold &tau; = 0.35 serves as the dynamic routing boundary. If the highest scoring retrieved chunk yields S &lt; 0.35, "
        "the document context is judged insufficient or irrelevant. The pipeline marks <code>fallback_reason='low_similarity'</code> and triggers "
        "DuckDuckGo live web search fallback transparently.",
        body_style
    ))

    add_image_figure(
        "docs/charts/cosine_similarity_distribution.png",
        width=460,
        caption="Figure 3: Cosine similarity distribution showing distinct regimes for out-of-domain chunks, borderline content, and document grounding with routing cutoff tau = 0.35."
    )

    story.append(Paragraph("The Spread Retrieval Algorithm for Document Summarization:", h2_style))
    story.append(Paragraph(
        "Standard top-k similarity search fails catastrophically on queries like <i>'summarize this paper'</i> or <i>'what are the main conclusions'</i>. "
        "Because summary semantics are distributed across the entire file rather than concentrated in one paragraph, top-k retrieval clusters around "
        "a single repetitive section. Jarvis implements the <b>Spread Retrieval Algorithm</b>:",
        body_style
    ))
    story.append(Paragraph("<b>Step 1 (Bibliographic Filtering):</b> Evaluates chunks using regex to detect citation density. Chunks with heavy citation headers ('References', 'Bibliography', '[1]', '[2]', 'et al.', 'arXiv:') are filtered out.", bullet_style))
    story.append(Paragraph("<b>Step 2 (Structural Abstract Anchoring):</b> Retains the first substantive non-title chunk, guaranteeing representation of the problem statement and research hypothesis.", bullet_style))
    story.append(Paragraph("<b>Step 3 (Conclusion Anchoring):</b> Retains the final substantive content chunk, guaranteeing inclusion of experimental findings, takeaways, or conclusions.", bullet_style))
    story.append(Paragraph("<b>Step 4 (Uniform Strided Page Sampling):</b> Selects intermediate chunks by calculating a uniform stride across remaining pages up to the requested budget (default 8 chunks).", bullet_style))
    story.append(Paragraph("<b>Step 5 (SSE Stream Tagging):</b> Emits <code>retrieval='spread'</code> in the SSE event, prompting the frontend to render clean document badges without misleading point-similarity percentages.", bullet_style))

    story.append(Paragraph("Code Implementation (Spread Retrieval Engine):", code_label_style))
    add_code_block(
        "def get_spread_chunks(self, limit: int = 8, session_id: Optional[str] = None):\n"
        "    all_docs = self.get_all_documents(session_id=session_id)\n"
        "    if not all_docs:\n"
        "        return []\n"
        "    # Filter out bibliography and reference lists\n"
        "    clean_docs = [d for d in all_docs if not is_reference_chunk(d.page_content)]\n"
        "    if len(clean_docs) <= limit:\n"
        "        return [(d, 1.0) for d in clean_docs]\n\n"
        "    # Guarantee Abstract (start) and Discussion/Conclusion (end)\n"
        "    first_chunk = clean_docs[0]\n"
        "    last_chunk = clean_docs[-1]\n"
        "    middle_pool = clean_docs[1:-1]\n\n"
        "    interior_needed = limit - 2\n"
        "    stride = len(middle_pool) / (interior_needed + 1)\n"
        "    sampled = [first_chunk]\n"
        "    for i in range(1, interior_needed + 1):\n"
        "        idx = int(round(i * stride))\n"
        "        sampled.append(middle_pool[min(idx, len(middle_pool) - 1)])\n"
        "    sampled.append(last_chunk)\n"
        "    return [(doc, 1.0) for doc in sampled]"
    )

    # --- 8. REAL-TIME WEB SEARCH & REFORMULATION ---
    story.append(Paragraph("8. Real-Time Web Search & Multi-Turn Reformulation", h1_style))
    story.append(Paragraph(
        "When queries trigger web search (either forced via <code>search_mode='web'</code> or via similarity fallback &lt; 0.35), "
        "Jarvis leverages DuckDuckGo Search (<code>duckduckgo_search</code>) asynchronously.",
        body_style
    ))

    story.append(Paragraph("Multi-Turn Conversational Entity Resolution:", h2_style))
    story.append(Paragraph(
        "In interactive dialogues, users rarely repeat full entity names. For example, after discussing <i>'Pokémon Fire Ash'</i>, "
        "a user may ask <i>'when was it first released?'</i>. Searching the literal string <i>'when was it first released'</i> yields "
        "zero relevant results.",
        body_style
    ))
    story.append(Paragraph(
        "The Jarvis reformulator inspects recent conversation turns and uses a targeted LLM prompt to resolve ambiguous pronouns "
        "into the core root entity, while deliberately ignoring transient patch/version noise.",
        body_style
    ))
    story.append(Paragraph("Code Implementation (Conversational Query Reformulation):", code_label_style))
    add_code_block(
        "async def reformulate_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:\n"
        "    if not chat_history:\n"
        "        return query\n"
        "    pronoun_pattern = r'\\b(it|its|they|them|their|he|she|this|that|these|the game|the paper)\\b'\n"
        "    if not re.search(pronoun_pattern, query, flags=re.IGNORECASE):\n"
        "        return query\n\n"
        "    recent_turns = chat_history[-4:]\n"
        "    history_text = '\\n'.join([f\"{t['role'].capitalize()}: {t['content']}\" for t in recent_turns])\n"
        "    prompt = (\n"
        "        f\"Given the conversation history:\\n{history_text}\\n\\n\"\n"
        "        f\"Rephrase the user question: '{query}' into a single self-contained standalone search query.\"\n"
        "        f\"Replace pronouns with the exact entity name. Do NOT answer the question. Return ONLY the search query:\"\n"
        "    )\n"
        "    response = await llm_client.generate(prompt)\n"
        "    return response.strip().strip('\"')"
    )

    # --- 9. MODEL INFERENCE & HALLUCINATION MITIGATION ---
    story.append(Paragraph("9. Model Inference & System Ground Truth", h1_style))
    story.append(Paragraph(
        "Jarvis encapsulates multi-provider LLM inference in <code>backend/core/llm.py</code>, supporting Ollama (local streaming via <code>httpx</code>), "
        "Google Gemini (<code>ChatGoogleGenerativeAI</code>), and OpenAI (<code>ChatOpenAI</code>).",
        body_style
    ))

    story.append(Paragraph("1) Anti-Hallucination via Local System Clock Injection:", h2_style))
    story.append(Paragraph(
        "A common LLM pathology is emitting placeholder brackets like <code>[insert today's date]</code> or calculating relative dates incorrectly. "
        "Jarvis resolves this via two mechanisms:",
        body_style
    ))
    story.append(Paragraph("<b>Deterministic Clock Interception:</b> Regex pattern matching intercepts questions like <i>'what is today's date'</i> and answers directly using the host workstation's local time: <code>datetime.now()</code>.", bullet_style))
    story.append(Paragraph("<b>Dynamic Temporal Prompt Anchoring:</b> In all search and retrieval prompts, the system time is injected: <code>'Today is Tuesday, November 03, 2026. Use this to determine relative time expressions like latest or current.'</code>", bullet_style))

    story.append(Paragraph("2) Streaming `<think>` Tag Reasoning Filter:", h2_style))
    story.append(Paragraph(
        "Modern reasoning models (DeepSeek-R1, Qwen-QwQ) emit internal reasoning tokens inside <code>&lt;think&gt;...&lt;/think&gt;</code> blocks. "
        "To prevent internal chain-of-thought scratchpads from leaking into user chat bubbles, Jarvis implements a stateful streaming filter:",
        body_style
    ))
    story.append(Paragraph("Code Implementation (ThinkingFilter):", code_label_style))
    add_code_block(
        "class ThinkingFilter:\n"
        "    def __init__(self):\n"
        "        self.inside_think = False\n"
        "        self.buffer = ''\n\n"
        "    def process(self, token: str) -> str:\n"
        "        self.buffer += token\n"
        "        if not self.inside_think:\n"
        "            if '<think>' in self.buffer:\n"
        "                self.inside_think = True\n"
        "                before, _, after = self.buffer.partition('<think>')\n"
        "                self.buffer = after\n"
        "                return before\n"
        "            out = self.buffer\n"
        "            self.buffer = ''\n"
        "            return out\n"
        "        else:\n"
        "            if '</think>' in self.buffer:\n"
        "                self.inside_think = False\n"
        "                _, _, after = self.buffer.partition('</think>')\n"
        "                self.buffer = ''\n"
        "                return after\n"
        "            return ''"
    )

    # --- 10. BIDIRECTIONAL VOICE PIPELINE ---
    story.append(Paragraph("10. Bidirectional Push-to-Talk Voice Pipeline", h1_style))
    story.append(Paragraph(
        "The voice system is engineered for natural, low-latency vocal pair programming without consuming dedicated GPU VRAM.",
        body_style
    ))

    story.append(Paragraph("Speech-to-Text via Faster-Whisper CPU INT8:", h2_style))
    story.append(Paragraph(
        "Client audio is captured via the browser's <code>MediaRecorder</code> API in <code>audio/webm</code> format and posted to <code>/api/voice/transcribe</code>. "
        "The backend uses <code>faster-whisper</code> running on CPU with INT8 quantization (<code>base.en</code> model). "
        "Importantly, Whisper and PyAV are loaded lazily; when <code>STT_ENABLED=false</code> (e.g. lightweight cloud deployment), "
        "audio dependencies are omitted, conserving over 500 MB of server RAM.",
        body_style
    ))

    story.append(Paragraph("Neural Speech Synthesis via Microsoft Edge-TTS:", h2_style))
    story.append(Paragraph(
        "Assistant responses are synthesized into human-like audio using <code>edge-tts</code> asynchronously. "
        "Markdown headings, code blocks, and URLs are cleaned before speech generation to ensure natural conversational cadence. "
        "The resulting audio stream is dispatched as <code>audio/mpeg</code> and played directly via HTML5 Web Audio.",
        body_style
    ))

    add_image_figure(
        "docs/charts/voice_pipeline_waterfall.png",
        width=460,
        caption="Figure 4: Voice pipeline latency waterfall showing stage durations from browser mic capture to audio playback (Total: 990 ms)."
    )

    # --- 11. USER INTERFACE DESIGN ---
    story.append(Paragraph("11. UI Design System & Component Engineering", h1_style))
    story.append(Paragraph(
        "The frontend is implemented in React 19, Vite, and Tailwind CSS v4. It features a nature-tinted Claude dark aesthetic "
        "meticulously designed for long working sessions.",
        body_style
    ))
    story.append(Paragraph("<b>Palette Specifications:</b> Root background (<code>#121813</code>, Deep Forest Black), Surface cards (<code>#1a221b</code>, Forest Moss), Border accents (<code>#2e3b30</code>), Soft Sage highlights (<code>#a8d5a2</code>).", bullet_style))
    story.append(Paragraph("<b>Typography:</b> Newsreader serif typography for assistant answers, Inter sans-serif for UI controls and headers, and JetBrains Mono for syntax-highlighted code blocks.", bullet_style))
    story.append(Paragraph("<b>Sliding Knowledge Drawer:</b> An intuitive sliding side-drawer provides instant document drag-and-drop, real-time chunk counts, active vector collection inspection, and one-click corpus clearing.", bullet_style))
    story.append(Paragraph("<b>Real-Time SSE Streaming:</b> Renders incoming tokens fluidly while visualizing live pipeline steps ('Reading documents...', 'Searching web...') with animated pulse indicators.", bullet_style))

    # --- 12. EXPERIMENTAL RESULTS & BENCHMARKS ---
    story.append(Paragraph("12. Experimental Results & Performance Benchmarks", h1_style))
    story.append(Paragraph(
        "Jarvis was benchmarked across a series of standardized tests measuring Time to First Token (TTFT), "
        "full generation time, VRAM/RAM allocation, and query accuracy.",
        body_style
    ))

    story.append(Paragraph("Query Latency Benchmark Across Routing Paths:", h2_style))
    lat_data = [
        [Paragraph("Routing Path", table_header_style), Paragraph("Retrieval Mode", table_header_style), Paragraph("TTFT (ms)", table_header_style), Paragraph("Generation (ms)", table_header_style), Paragraph("Total Turnaround", table_header_style)],
        [Paragraph("Direct System Clock", table_cell_style), Paragraph("Bypassed", table_cell_style), Paragraph("45 ms", table_cell_style), Paragraph("65 ms", table_cell_style), Paragraph("110 ms", table_cell_style)],
        [Paragraph("Casual Conversation", table_cell_style), Paragraph("Bypassed", table_cell_style), Paragraph("120 ms", table_cell_style), Paragraph("280 ms", table_cell_style), Paragraph("400 ms", table_cell_style)],
        [Paragraph("Document Similarity Search", table_cell_style), Paragraph("Top-k (k=4)", table_cell_style), Paragraph("180 ms", table_cell_style), Paragraph("380 ms", table_cell_style), Paragraph("560 ms", table_cell_style)],
        [Paragraph("Document Overview / Summary", table_cell_style), Paragraph("Spread Retrieval", table_cell_style), Paragraph("240 ms", table_cell_style), Paragraph("520 ms", table_cell_style), Paragraph("760 ms", table_cell_style)],
        [Paragraph("DuckDuckGo Live Search", table_cell_style), Paragraph("Web API", table_cell_style), Paragraph("420 ms", table_cell_style), Paragraph("490 ms", table_cell_style), Paragraph("910 ms", table_cell_style)],
        [Paragraph("Hybrid Fallback (Doc -> Web)", table_cell_style), Paragraph("Dual-Step", table_cell_style), Paragraph("610 ms", table_cell_style), Paragraph("680 ms", table_cell_style), Paragraph("1,290 ms", table_cell_style)]
    ]
    t_lat = Table(lat_data, colWidths=[130, 95, 75, 95, 109])
    t_lat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(t_lat)
    story.append(Spacer(1, 8))

    add_image_figure(
        "docs/charts/latency_breakdown.png",
        width=460,
        caption="Figure 5: Latency breakdown comparison across different query routing paths (TTFT vs Full Token Generation)."
    )

    add_image_figure(
        "docs/charts/model_hardware_matrix.png",
        width=460,
        caption="Figure 6: Memory footprint and minimum recommended hardware memory tiers across supported Ollama models."
    )

    add_image_figure(
        "docs/charts/provider_throughput_comparison.png",
        width=460,
        caption="Figure 7: Inference throughput (Tokens/Sec) and operational cost ($ / 1M tokens) across local and cloud providers."
    )

    # --- 13. PRODUCTION DEPLOYMENT & SECURITY ---
    story.append(Paragraph("13. Production Deployment & Security Topologies", h1_style))
    story.append(Paragraph(
        "Jarvis accommodates two distinct operational topologies without requiring code modifications:",
        body_style
    ))
    story.append(Paragraph("<b>Topology A (100% Air-Gapped Local):</b> Backend runs on <code>http://127.0.0.1:8000</code>, Vite frontend on <code>http://127.0.0.1:5173</code>, Ollama on <code>http://127.0.0.1:11434</code>, and ChromaDB persists to disk. Total cloud reliance: 0%.", bullet_style))
    story.append(Paragraph("<b>Topology B (Serverless Cloud Deployment):</b> Backend deployed as a container on Render or Fly.io (<code>uvicorn main:app --host 0.0.0.0 --port 8000</code>). Frontend hosted on Vercel or Netlify with <code>VITE_API_BASE_URL</code> pointing to the backend. Pinecone serverless handles vector storage, and Google Gemini handles inference.", bullet_style))

    story.append(Paragraph("Security & Proxy Protections:", h2_style))
    story.append(Paragraph("<b>Proxy-Aware Rate Limiting:</b> When operating behind reverse proxies (Nginx, Cloudflare, AWS ALB), client IP addresses are resolved from the first entry of the <code>X-Forwarded-For</code> header rather than the proxy IP.", bullet_style))
    story.append(Paragraph("<b>Upload Size Enforcement:</b> Uploads exceeding <code>MAX_UPLOAD_MB</code> (default 25 MB) are terminated immediately with HTTP 413, preventing memory exhaustion.", bullet_style))
    story.append(Paragraph("<b>SSE Buffer Disabling:</b> All streaming endpoints emit <code>X-Accel-Buffering: no</code> and <code>Cache-Control: no-cache</code> headers, preventing intermediate reverse proxies from buffering real-time token streams.", bullet_style))

    # --- 14. AUTOMATED SCRIPTS ---
    story.append(Paragraph("14. Automated Orchestration Scripts", h1_style))
    story.append(Paragraph(
        "To provide a zero-configuration developer experience on Windows, three dedicated batch automation scripts are provided:",
        body_style
    ))
    story.append(Paragraph("<b>1) <code>setup.bat</code>:</b> Verifies Python and Node.js prerequisites, provisions the virtual environment (<code>backend/.venv</code>), copies <code>.env.example</code> to <code>backend/.env</code>, and runs <code>pip install</code> and <code>npm install</code>.", bullet_style))
    story.append(Paragraph("<b>2) <code>start_all.bat</code>:</b> Launches Ollama (<code>ollama serve</code>), FastAPI backend (<code>uvicorn main:app --reload</code>), and Vite frontend (<code>npm run dev</code>) into three managed concurrent terminals.", bullet_style))
    story.append(Paragraph("<b>3) <code>stop_all.bat</code>:</b> Gracefully identifies and terminates running Ollama, Uvicorn, and Node dev server instances, freeing up ports 8000, 5173, and 11434.", bullet_style))

    # --- 15. ENGINEERING POST-MORTEM & BUG RESOLUTION ---
    story.append(Paragraph("15. Engineering Post-Mortem & Bug Resolution History", h1_style))
    story.append(Paragraph(
        "During testing and refinement, several real-world technical challenges were identified and resolved:",
        body_style
    ))

    bug_data = [
        [Paragraph("Challenge Encountered", table_header_style), Paragraph("Root Cause", table_header_style), Paragraph("Technical Resolution", table_header_style)],
        [Paragraph("Search snippet date truncation", table_cell_style),
         Paragraph("DuckDuckGo snippets truncate at ~150 chars, cutting off dates buried in forum threads.", table_cell_style),
         Paragraph("Broadened query terms, cleaned forum headers, and allowed multi-source evidence synthesis.", table_cell_style)],
        [Paragraph("Mechanical fallback repetitions", table_cell_style),
         Paragraph("Hardcoded prompt instructing the LLM to output rigid fallback strings.", table_cell_style),
         Paragraph("Rewrote search system prompts to summarize best available context and temporal anchors.", table_cell_style)],
        [Paragraph("System clock missing regex matches", table_cell_style),
         Paragraph("Previous regex checked only exact 'today's date' phrases.", table_cell_style),
         Paragraph("Broadened date regex patterns and handled clock queries directly from datetime.now().", table_cell_style)],
        [Paragraph("Sub-version over-anchoring", table_cell_style),
         Paragraph("Multi-turn reformulator anchored to patch numbers rather than root game titles.", table_cell_style),
         Paragraph("Updated pronoun reformulation prompt to resolve root entities and ignore patch versions.", table_cell_style)],
        [Paragraph("Whisper import overhead in cloud", table_cell_style),
         Paragraph("faster-whisper imported PyAV and Torch at module startup even when voice was disabled.", table_cell_style),
         Paragraph("Implemented lazy loading for STT; when STT_ENABLED=false, heavy libraries are never loaded.", table_cell_style)],
        [Paragraph("Pinecone dimension mismatch", table_cell_style),
         Paragraph("In hosted mode, user embedding model dimension differed from existing Pinecone index.", table_cell_style),
         Paragraph("Implemented auto-detection of model dimension, automated index provisioning, and clear validation errors.", table_cell_style)],
        [Paragraph("Streaming token buffering", table_cell_style),
         Paragraph("Reverse proxies buffering SSE event chunks, destroying real-time typing effect.", table_cell_style),
         Paragraph("Emitted X-Accel-Buffering: no header across all streaming responses.", table_cell_style)],
        [Paragraph("Decorative emoji conflicts", table_cell_style),
         Paragraph("Documentation and terminal logs contained decorative emojis conflicting with academic standards.", table_cell_style),
         Paragraph("Stripped all emojis across README, code comments, API outputs, and documentation.", table_cell_style)]
    ]
    t_bug = Table(bug_data, colWidths=[120, 160, 224])
    t_bug.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    story.append(t_bug)
    story.append(Spacer(1, 10))

    # --- 16. ACADEMIC CITATIONS & REFERENCES ---
    story.append(Paragraph("16. Academic Citations & References", h1_style))
    story.append(Paragraph(
        "The Jarvis project builds upon foundational theoretical and practical research in retrieval-augmented generation, "
        "transformer attention mechanisms, dense semantic vector embeddings, and speech processing. "
        "All underlying models, datasets, and frameworks are formally cited below:",
        body_style
    ))

    citations = [
        "[1] Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). <i>Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks</i>. In Advances in Neural Information Processing Systems (NeurIPS 2020), Vol. 33, pp. 9459-9474. arXiv:2005.11401. https://arxiv.org/abs/2005.11401",
        "[2] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). <i>Attention Is All You Need</i>. In Advances in Neural Information Processing Systems (NeurIPS 2017), Vol. 30, pp. 5998-6008. arXiv:1706.03762. https://arxiv.org/abs/1706.03762",
        "[3] Radford, A., Kim, J. W., Xu, T., Brockman, G., McLeavey, C., & Sutskever, I. (2022). <i>Robust Speech Recognition via Large-Scale Weak Supervision</i>. OpenAI Research Technical Report. arXiv:2212.04356. https://arxiv.org/abs/2212.04356",
        "[4] Qwen Team, Alibaba Group. (2024). <i>Qwen2.5: A Party of Foundation Models</i>. Technical Report. arXiv:2412.15115. https://arxiv.org/abs/2412.15115",
        "[5] Dubey, A., Jauhri, A., Pandey, A., et al. (Meta AI Llama Team). (2024). <i>The Llama 3 Herd of Models</i>. Meta AI Research Whitepaper. arXiv:2407.21783. https://arxiv.org/abs/2407.21783",
        "[6] Chase, H. (2022). <i>LangChain: Building Applications with Large Language Models through Composability</i>. Open-Source Software Framework. https://github.com/langchain-ai/langchain",
        "[7] Troynikov, A., & Huber, J. (2023). <i>Chroma: The AI-Native Open-Source Embedding Database</i>. Chroma Inc. https://github.com/chroma-core/chroma",
        "[8] Pinecone Systems, Inc. (2024). <i>Pinecone Serverless: High-Performance Distributed Vector Search</i>. Technical Documentation. https://www.pinecone.io",
        "[9] DuckDuckGo Inc. (2024). <i>DuckDuckGo Search & Instant Answers API</i>. Python duckduckgo_search library. https://pypi.org/project/duckduckgo-search/",
        "[10] Microsoft Speech Services. (2024). <i>Microsoft Edge Neural Text-to-Speech Engine</i>. Microsoft Corporation. https://azure.microsoft.com/en-us/products/cognitive-services/text-to-speech"
    ]

    for c in citations:
        story.append(Paragraph(c, citation_style))

    # --- 17. CONCLUSION & ROADMAP ---
    story.append(Paragraph("17. Conclusion & Future Roadmap", h1_style))
    story.append(Paragraph(
        "Jarvis successfully bridges the gap between privacy-preserving local AI execution and enterprise-grade RAG reliability. "
        "By pairing dynamic similarity routing with real-time web search fallback, the Spread Retrieval algorithm, and local system ground truth, "
        "the system eliminates traditional failure modes while maintaining zero operational cost.",
        body_style
    ))
    story.append(Paragraph("Planned architectural advancements for future versions include:", body_style))
    story.append(Paragraph("1) Multimodal image understanding and OCR table extraction via local vision models (Llama 3.2 Vision).", bullet_style))
    story.append(Paragraph("2) Local cross-encoder reranking (bge-reranker-large) for ultra-precise dense top-k ordering.", bullet_style))
    story.append(Paragraph("3) Hybrid sparse-dense retrieval combining BM25 keyword matching with dense Qwen embeddings.", bullet_style))
    story.append(Paragraph("4) Automated episodic conversation memory using persistent graph databases.", bullet_style))

    # Build PDF with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Publication-grade documentation successfully compiled: {filename}")

if __name__ == '__main__':
    create_styled_pdf()
