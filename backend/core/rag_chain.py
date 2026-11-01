import json
import logging
from typing import AsyncGenerator, List, Dict, Any
from config import settings
from core.vectorstore import vector_store_manager
from core.search import web_search_engine
from core.llm import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_RAG = """You are an advanced, intelligent AI Assistant with access to grounded context.
Your goal is to provide accurate, concise, and helpful answers based on the provided references.

Rules:
1. Prioritize the provided Grounded Context to answer questions.
2. If citing information, clearly reference the source.
3. Use clean GitHub-flavored markdown with code formatting when sharing code.
4. If the context does not fully answer the question, state what is known from the context and supplement with your general knowledge, stating the difference clearly.
"""

SYSTEM_PROMPT_SEARCH = """You are an advanced, helpful AI Assistant equipped with live web search results.
Synthesize the provided live web search results into a clean, comprehensive, up-to-date answer.

Rules:
1. Directly answer the user's question using the live web search sources.
2. Include clickable markdown links to sources when relevant (e.g. [Source Title](URL)).
3. Structure your response with clear headings or bullet points if explaining complex events or technical topics.
"""

class RAGPipeline:
    @property
    def threshold(self) -> float:
        return settings.SIMILARITY_SCORE_THRESHOLD

    async def stream_query(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Processes user query through the Dual RAG + Web Search pipeline.
        Yields Server-Sent Events (SSE) format strings:
        - metadata with sources
        - individual response tokens
        - done signal
        """
        chat_history = chat_history or []
        stats = vector_store_manager.get_stats()
        total_chunks = stats.get("total_chunks", 0)

        sources: List[Dict[str, Any]] = []
        source_type = "direct"
        context_text = ""
        system_prompt = SYSTEM_PROMPT_RAG

        # Step 1: Check Local ChromaDB if documents are loaded
        if total_chunks > 0:
            doc_results = vector_store_manager.search_with_scores(query, k=settings.SIMILARITY_K)
            
            if doc_results:
                best_score = max([score for _, score in doc_results])
                logger.info(f"ChromaDB search best score: {best_score:.4f} (Threshold: {self.threshold})")

                if best_score >= self.threshold:
                    source_type = "document"
                    context_blocks = []
                    for doc, score in doc_results:
                        src_name = doc.metadata.get("source", "Uploaded Document")
                        page = doc.metadata.get("page", 1)
                        context_blocks.append(f"--- Document: {src_name} (Page/Chunk: {page}) ---\n{doc.page_content}")
                        sources.append({
                            "title": f"{src_name} (Page {page})",
                            "snippet": doc.page_content[:200] + "...",
                            "source_type": "document",
                            "score": round(score, 3)
                        })
                    context_text = "\n\n".join(context_blocks)

        # Step 2: Fallback to Autonomous DuckDuckGo Search if no document match
        if source_type != "document":
            logger.info(f"Local docs insufficient or absent. Initiating DuckDuckGo fallback search for: '{query}'")
            search_results = web_search_engine.search(query)
            
            if search_results:
                source_type = "web"
                context_text = web_search_engine.format_search_context(search_results)
                sources = search_results
                system_prompt = SYSTEM_PROMPT_SEARCH

        # Step 3: Yield Sources Metadata Event
        init_event = {
            "type": "sources",
            "source_type": source_type,
            "sources": sources
        }
        yield f"data: {json.dumps(init_event)}\n\n"

        # Step 4: Construct Prompt with Context
        augmented_messages: List[Dict[str, str]] = []
        
        # Include past few conversation turns
        if chat_history:
            augmented_messages.extend(chat_history[-6:])

        if context_text:
            augmented_query = f"Grounded Context:\n{context_text}\n\nUser Question: {query}"
        else:
            augmented_query = query

        augmented_messages.append({"role": "user", "content": augmented_query})

        # Step 5: Stream Tokens from Local Ollama GPU
        async for token in llm_client.stream_chat(augmented_messages, system_prompt=system_prompt):
            token_event = {
                "type": "token",
                "content": token
            }
            yield f"data: {json.dumps(token_event)}\n\n"

        # Step 6: Stream Done Signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

rag_pipeline = RAGPipeline()
