import os
import json
import logging
import re
from urllib.parse import urlparse
from datetime import datetime
from typing import AsyncGenerator, List, Dict, Any, Optional
from config import settings
from core.vectorstore import vector_store_manager
from core.search import web_search_engine
from core.llm import llm_client

logger = logging.getLogger(__name__)

def get_current_system_context() -> str:
    """
    Returns the real-time local date, time, and day of week.
    Prevents the LLM from hallucinating placeholders like [insert today's date].
    """
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p (Local System Time)")

def is_datetime_query(query: str) -> bool:
    """
    Checks if the user is asking specifically about current date, day, or time.
    """
    q = query.lower().strip()
    datetime_patterns = [
        r'\b(what day is it|what is today|what\'s the date|current date|today\'s date|what time is it|current time|correct time)\b'
    ]
    for pattern in datetime_patterns:
        if re.search(pattern, q):
            return True
    return False

def is_casual_conversation(query: str) -> bool:
    """
    Identifies greetings, pleasantries, small talk, and direct capability queries.
    These must be answered directly by the LLM with path "direct", not routed to web search.
    """
    q = query.lower().strip()
    q_clean = re.sub(r'[^\w\s]', '', q).strip()

    casual_patterns = [
        r'^(hi|hello|hey|howdy|sup|yo|greetings|good\s+(morning|afternoon|evening|day|night))$',
        r'^(how\s+are\s+you(\s+today)?|how\s+is\s+it\s+going|hows\s+it\s+going|whats\s+up|how\s+do\s+you\s+do)$',
        r'^(thank\s+you|thanks(\s+a\s+lot)?|thx|much\s+appreciated|appreciate\s+it)$',
        r'^(ready|are\s+you\s+ready|test|testing(\s+1\s+2\s+3)?|ping|can\s+you\s+hear\s+me)$',
        r'^(who\s+are\s+you|what\s+can\s+you\s+do|what\s+are\s+your\s+capabilities|introduce\s+yourself)$',
        r'^(bye|goodbye|see\s+you|have\s+a\s+good\s+day)$',
        r'^(tell\s+me\s+a\s+joke|write\s+a\s+poem)$'
    ]
    return any(re.search(p, q_clean) for p in casual_patterns)

def is_realtime_query(query: str) -> bool:
    """
    Checks if the user query is asking for live external info:
    news, prices, weather, scores, or "latest/current/now" combined with a topic.
    The bare word "today" alone does NOT trigger web search.
    """
    q = query.lower().strip()
    patterns = [
        r'\b(news|weather|forecast|stock\s+price|crypto|bitcoin|election|score|sports|match\s+score)\b',
        r'\b(latest\s+(version|release|update|news|model|phone|game|movie|patch|build))\b',
        r'\b(current\s+(price|status|rate|events|president|ceo|champion|weather))\b',
        r'\b(who\s+won|what\s+happened\s+(yesterday|today|recently))\b',
        r'\b(release\s+date\s+(of|for)|when\s+is\s+.*(releasing|released))\b',
        r'\b(what\s+is\s+happening\s+with|live\s+coverage)\b'
    ]
    return any(re.search(p, q) for p in patterns)

def is_summary_query(query: str) -> bool:
    """
    Checks if the user query is asking for a document-level summary, overview,
    breakdown, analysis, key takeaways, or main points across the indexed documents.
    """
    q = query.lower().strip()
    summary_patterns = [
        r'\b(summarize|summarise|summary)\b',
        r'\b(overview|key findings|main points|key takeaways|executive summary)\b',
        r'\b(what is this (paper|doc|document|pdf) about)\b',
        r'\b(what are (these|the) (papers|docs|documents|pdfs) about)\b',
        r'\b(what does this (paper|doc|document|pdf) (talk|say) about)\b',
        r'\b(explain (this|the) (paper|document|pdf))\b',
        r'\b(tell me about (this|the) (paper|document|pdf))\b',
        r'\b(give me a summary|brief overview)\b',
        r'\b(analy[zs]e)\b.*?\b(paper|document|doc|pdf|work)\b',
        r'\banalysis\s+of\b.*?\b(paper|document|doc|pdf|work)\b',
        r'\bbreak\s*down\b.*?\b(paper|document|doc|pdf|work)\b',
        r'\b(analy[zs]e|break\s*down)\s+(this|the|my)?\s*(paper|doc|document|pdf)\b',
        r'\b(analysis|breakdown)\s+of\s+(this|the|my)?\s*(paper|doc|document|pdf)\b'
    ]
    return any(re.search(p, q) for p in summary_patterns)

SYSTEM_PROMPT_DIRECT = """You are an advanced, intelligent Local RAG & Voice AI Assistant.
System Knowledge & Environment:
- Real-Time Clock: {current_time}
- Hardware: Hardware-accelerated local execution with zero cloud telemetry.
- Capabilities: Live Web Search (DuckDuckGo), Document RAG (ChromaDB + Pinecone), and Neural TTS Voice.

Rules:
1. If the user asks for the current date, day, or time, answer directly and accurately using the Real-Time Clock provided above. Never use placeholder brackets like [insert date] or [insert time].
2. If asked about your capabilities, confirm enthusiastically and explain your available features (Auto Smart RAG, Forced Web Search, Documents Only, and Push-to-Talk Voice).
3. Format your answers in clean, professional GitHub-flavored markdown.
4. Be concise, direct, helpful, and polite.
"""

SYSTEM_PROMPT_RAG = """You are an advanced, intelligent AI Assistant with access to grounded context from uploaded documents.
System Knowledge:
- Real-Time Clock: {current_time}

Rules:
1. Prioritize the provided Grounded Context to answer questions.
2. If citing information, clearly reference the source document and page/chunk.
3. Use clean GitHub-flavored markdown with code formatting when sharing code.
4. If the context does not fully answer the question, state what is known from the context and supplement with your general knowledge, stating the difference clearly.
"""

SYSTEM_PROMPT_SEARCH = """You are an advanced, helpful AI Assistant equipped with live web search results.
System Knowledge:
- Real-Time Clock: {current_time}

Rules:
1. Directly answer the user's question using the live web search sources.
2. Include clickable markdown links to sources when relevant (e.g. [Source Title](URL)).
3. Structure your response with clear headings or bullet points if explaining complex events or technical topics.
4. If asked about the current date or time, reference the Real-Time Clock above.
"""

class RAGPipeline:
    @property
    def threshold(self) -> float:
        return settings.SIMILARITY_SCORE_THRESHOLD

    async def reformulate_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Reformulates conversational queries with pronouns (e.g. 'what is its latest version')
        into a standalone self-contained search query using recent conversation turns.
        """
        if not chat_history:
            return query

        # Fast check if query contains ambiguous pronouns or references
        pronoun_pattern = r'\b(it|its|they|them|their|he|she|this|that|these|those|the game|the paper|the company|the tool)\b'
        if not re.search(pronoun_pattern, query, flags=re.IGNORECASE):
            return query

        # Use LLM to resolve pronouns into standalone search query
        recent_turns = chat_history[-4:]
        history_text = "\n".join([f"{t['role'].capitalize()}: {t['content']}" for t in recent_turns])

        prompt = (
            f"Given the conversation history and the latest user question, rephrase the user question "
            f"into a single, self-contained search query that replaces pronouns ('it', 'its', 'that') with "
            f"the actual entity name mentioned in the history.\n"
            f"Output ONLY the standalone rephrased search query. Do not add quotes, explanations, or punctuation at the start.\n\n"
            f"Conversation History:\n{history_text}\n\n"
            f"User Question: {query}\n"
            f"Standalone Query:"
        )

        try:
            rephrased = ""
            async for token in llm_client.stream_chat([{"role": "user", "content": prompt}]):
                rephrased += token
            rephrased = rephrased.strip().strip('"').strip("'")
            if rephrased and len(rephrased) > 3 and not rephrased.startswith("Given"):
                logger.info(f"Query reformulated: '{query}' -> '{rephrased}'")
                return rephrased
        except Exception as e:
            logger.warning(f"Query reformulation error: {e}")

        return query

    async def stream_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        search_mode: str = "auto",
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Processes user query through the Dual RAG + Web Search pipeline.
        Yields Server-Sent Events (SSE) format strings:
        - status: Live visual pipeline steps (e.g. 'Searching web...', 'Reading documents...')
        - sources: Metadata with sources list
        - token: Individual streamed tokens
        - done: Completion signal
        """
        chat_history = chat_history or []
        current_time_str = get_current_system_context()

        # Step 0: Check for direct Date/Time question
        if is_datetime_query(query):
            yield f"data: {json.dumps({'type': 'status', 'message': 'Checking system clock...'})}\n\n"
            yield f"data: {json.dumps({
                'type': 'sources',
                'source_type': 'direct',
                'path': 'direct',
                'fallback_reason': 'realtime_query',
                'best_score': None,
                'threshold': self.threshold,
                'sources': []
            })}\n\n"
            
            now = datetime.now()
            time_resp = f"📅 **Today is {now.strftime('%A, %B %d, %Y')}**.\n\n⏰ The current local time is **{now.strftime('%I:%M:%S %p')}**."
            for word in time_resp.split(" "):
                yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # Step 0b: Check for casual conversation / small talk (answered directly by LLM)
        if search_mode == "auto" and is_casual_conversation(query):
            yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"
            yield f"data: {json.dumps({
                'type': 'sources',
                'source_type': 'direct',
                'path': 'direct',
                'fallback_reason': None,
                'best_score': None,
                'threshold': self.threshold,
                'sources': []
            })}\n\n"

            augmented_messages: List[Dict[str, str]] = []
            if chat_history:
                augmented_messages.extend(chat_history[-6:])
            augmented_messages.append({"role": "user", "content": query})

            system_prompt = SYSTEM_PROMPT_DIRECT.format(current_time=current_time_str)
            async for token in llm_client.stream_chat(augmented_messages, system_prompt=system_prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        # Step 1: Query Reformulation for Multi-turn conversation
        standalone_query = query
        if chat_history:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Resolving conversation context...'})}\n\n"
            standalone_query = await self.reformulate_query(query, chat_history)

        stats = vector_store_manager.get_stats(session_id=session_id)
        total_chunks = stats.get("total_chunks", 0)

        sources: List[Dict[str, Any]] = []
        source_type = "direct"
        path = "direct"
        retrieval: Optional[str] = None
        fallback_reason: Optional[str] = None
        best_score: Optional[float] = None
        context_text = ""
        system_prompt = SYSTEM_PROMPT_DIRECT.format(current_time=current_time_str)

        # Helper to construct structured document source records
        # SCORE SEMANTICS:
        # 'score' is cosine SIMILARITY (relevance score in [0.0, 1.0]), NOT distance.
        # Higher score = more relevant/similar (1.0 = identical match, 0.0 = completely dissimilar).
        def format_doc_source(doc: Any, sc: float) -> Dict[str, Any]:
            src_name = doc.metadata.get("source", "Uploaded Document")
            fname = os.path.basename(src_name)
            raw_pg = doc.metadata.get("page")
            is_pdf = fname.lower().endswith(".pdf")
            page_val = int(raw_pg) if (is_pdf and raw_pg is not None) else None
            title_val = f"{fname} (Page {raw_pg})" if (is_pdf and raw_pg is not None) else fname
            content_str = doc.page_content.strip()
            snippet_val = content_str[:240] + ("..." if len(content_str) > 240 else "")

            return {
                "title": title_val,
                "filename": fname,
                "page": page_val,
                "snippet": snippet_val,
                "source_type": "document",
                "score": round(float(sc), 3)  # Normalized cosine similarity [0.0, 1.0]
            }

        # Helper to construct structured web source records
        def format_web_source(item: Dict[str, Any]) -> Dict[str, Any]:
            url_val = item.get("url") or item.get("href") or ""
            domain_val = item.get("domain", "")
            if not domain_val and url_val:
                try:
                    from urllib.parse import urlparse
                    domain_val = urlparse(url_val).netloc.replace("www.", "")
                except Exception:
                    domain_val = ""
            return {
                "title": item.get("title", "Untitled Source"),
                "url": url_val,
                "domain": domain_val,
                "snippet": item.get("snippet") or item.get("body") or "",
                "source_type": "web"
            }

        # Check for Document Summary / Overview Request (skip similarity threshold, sample across corpus)
        if search_mode in ["auto", "docs"] and total_chunks > 0 and is_summary_query(standalone_query):
            path = "document"
            source_type = "document"
            retrieval = "spread"
            fallback_reason = None
            best_score = 1.0  # Intentional multi-page corpus synthesis
            yield f"data: {json.dumps({'type': 'status', 'message': 'Synthesizing document overview across pages...'})}\n\n"
            spread_docs = vector_store_manager.get_spread_chunks(limit=8, session_id=session_id)
            context_blocks = []
            for doc, sc in spread_docs:
                src_name = doc.metadata.get("source", "Uploaded Document")
                page = doc.metadata.get("page", 1)
                context_blocks.append(f"--- Document: {src_name} (Page/Chunk: {page}) ---\n{doc.page_content}")
                sources.append(format_doc_source(doc, sc))
            context_text = "\n\n".join(context_blocks)
            system_prompt = SYSTEM_PROMPT_RAG.format(current_time=current_time_str)

        # MODE: Forced Web Search
        elif search_mode == "web":
            path = "web"
            retrieval = "similarity"
            fallback_reason = "forced_web"
            yield f"data: {json.dumps({'type': 'status', 'message': f'Searching the web for: \"{standalone_query}\"...'})}\n\n"
            search_results = web_search_engine.search(standalone_query)
            if search_results:
                source_type = "web"
                context_text = web_search_engine.format_search_context(search_results)
                sources = [format_web_source(r) for r in search_results]
                system_prompt = SYSTEM_PROMPT_SEARCH.format(current_time=current_time_str)

        # MODE: Forced Documents Only
        elif search_mode == "docs":
            backend_name = "Pinecone" if vector_store_manager.vector_backend == "pinecone" else "ChromaDB"
            yield f"data: {json.dumps({'type': 'status', 'message': f'Searching uploaded documents in {backend_name}...'})}\n\n"
            if total_chunks > 0:
                retrieval = "similarity"
                doc_results = vector_store_manager.search_with_scores(standalone_query, k=settings.SIMILARITY_K, session_id=session_id)
                if doc_results:
                    path = "document"
                    source_type = "document"
                    raw_best = float(max([s for _, s in doc_results]))
                    best_score = round(raw_best, 3)
                    fallback_reason = "low_confidence" if raw_best < self.threshold else None
                    context_blocks = []
                    for doc, score in doc_results:
                        src_name = doc.metadata.get("source", "Uploaded Document")
                        page = doc.metadata.get("page", 1)
                        context_blocks.append(f"--- Document: {src_name} (Page/Chunk: {page}) ---\n{doc.page_content}")
                        sources.append(format_doc_source(doc, score))
                    context_text = "\n\n".join(context_blocks)
                    system_prompt = SYSTEM_PROMPT_RAG.format(current_time=current_time_str)
                else:
                    path = "direct"
                    fallback_reason = "low_confidence"
            else:
                path = "direct"
                fallback_reason = "empty_store"

        # MODE: Auto (Smart RAG + Fallback)
        else:
            if total_chunks > 0:
                yield f"data: {json.dumps({'type': 'status', 'message': 'Checking uploaded documents...'})}\n\n"
                doc_results = vector_store_manager.search_with_scores(standalone_query, k=settings.SIMILARITY_K, session_id=session_id)
                if doc_results:
                    raw_best = float(max([s for _, s in doc_results]))
                    best_score = round(raw_best, 3)
                    logger.info(f"ChromaDB search best score (similarity): {best_score:.4f} (Threshold: {self.threshold})")

                    if raw_best >= self.threshold:
                        path = "document"
                        source_type = "document"
                        retrieval = "similarity"
                        fallback_reason = None
                        context_blocks = []
                        for doc, score in doc_results:
                            src_name = doc.metadata.get("source", "Uploaded Document")
                            page = doc.metadata.get("page", 1)
                            context_blocks.append(f"--- Document: {src_name} (Page/Chunk: {page}) ---\n{doc.page_content}")
                            sources.append(format_doc_source(doc, score))
                        context_text = "\n\n".join(context_blocks)
                        system_prompt = SYSTEM_PROMPT_RAG.format(current_time=current_time_str)
                    else:
                        fallback_reason = "low_confidence"
                else:
                    fallback_reason = "low_confidence"
            else:
                fallback_reason = "empty_store"

            # Fallback to Live DuckDuckGo Web Search if no document match
            if path != "document":
                if is_realtime_query(standalone_query):
                    fallback_reason = "realtime_query"
                yield f"data: {json.dumps({'type': 'status', 'message': f'Searching live web for: \"{standalone_query}\"...'})}\n\n"
                search_results = web_search_engine.search(standalone_query)
                if search_results:
                    path = "web"
                    source_type = "web"
                    retrieval = "similarity"
                    context_text = web_search_engine.format_search_context(search_results)
                    sources = [format_web_source(r) for r in search_results]
                    system_prompt = SYSTEM_PROMPT_SEARCH.format(current_time=current_time_str)

        # Yield Sources Metadata Event
        # SCORE SEMANTICS:
        # 'best_score' and source 'score' are cosine SIMILARITY in [0.0, 1.0], NOT distance.
        # Higher score = more similar/relevant (1.0 = identical, 0.0 = completely dissimilar).
        # Compared against 'threshold' (0.45) to determine if local documents have confident relevance.
        init_event = {
            "type": "sources",
            "source_type": source_type,
            "path": path,
            "retrieval": retrieval,
            "fallback_reason": fallback_reason,
            "best_score": best_score,
            "threshold": self.threshold,
            "sources": sources
        }
        yield f"data: {json.dumps(init_event)}\n\n"

        # Construct Prompt with Context
        augmented_messages: List[Dict[str, str]] = []
        if chat_history:
            augmented_messages.extend(chat_history[-6:])

        if context_text:
            augmented_query = f"Grounded Context:\n{context_text}\n\nUser Question: {query}"
        else:
            augmented_query = query

        augmented_messages.append({"role": "user", "content": augmented_query})

        yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...'})}\n\n"

        # Stream Tokens from Local Ollama
        async for token in llm_client.stream_chat(augmented_messages, system_prompt=system_prompt):
            token_event = {
                "type": "token",
                "content": token
            }
            yield f"data: {json.dumps(token_event)}\n\n"

        # Done Signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

rag_pipeline = RAGPipeline()
