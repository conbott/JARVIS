import re
import logging
from typing import List, Dict, Any
from ddgs import DDGS

logger = logging.getLogger(__name__)

class WebSearchEngine:
    def __init__(self, max_results: int = 4):
        self.max_results = max_results

    def clean_search_query(self, query: str) -> str:
        """
        Strips conversational framing so search engines get clean keyword queries.
        e.g. 'can you search the web for quantum computing 2026' -> 'quantum computing 2026'
        """
        cleaned = query.strip()
        # Remove common conversational prefixes
        patterns = [
            r'^(can you|could you|please|kindly)?\s*(do a\s+)?(search(\s+the|\s+on|\s+for|\s+web)*\s*:?\s*)',
            r'^(what is|who is|tell me about|find info on|look up|give me information on)\s+'
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()

        # If stripping emptied the query, fallback to original
        return cleaned if len(cleaned) > 2 else query

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a live web search using DuckDuckGo via DDGS with zero API keys required.
        Returns a list of structured source records: title, url, snippet.
        """
        results: List[Dict[str, Any]] = []
        cleaned_query = self.clean_search_query(query)
        
        # Try cleaned query first, then fallback to original query if needed
        query_candidates = [cleaned_query]
        if cleaned_query.lower() != query.lower():
            query_candidates.append(query)

        for q in query_candidates:
            try:
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(q, max_results=self.max_results))
                    if raw_results:
                        for item in raw_results:
                            href = item.get("href", "")
                            domain = ""
                            if href:
                                try:
                                    from urllib.parse import urlparse
                                    domain = urlparse(href).netloc.replace("www.", "")
                                except Exception:
                                    domain = ""
                            results.append({
                                "title": item.get("title", "Untitled Source"),
                                "url": href,
                                "domain": domain,
                                "snippet": item.get("body", ""),
                                "source_type": "web"
                            })
                        logger.info(f"DDGS web search succeeded for '{q}': {len(results)} results found.")
                        return results
            except Exception as e:
                logger.warning(f"DDGS attempt failed for '{q}': {e}")

        logger.info(f"No DDGS search results found for query: '{query}'")
        return results

    def format_search_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Formats search results into an LLM context block with numbered citations.
        """
        if not search_results:
            return "No web search results available."
        
        context_parts = []
        for i, res in enumerate(search_results, start=1):
            context_parts.append(
                f"[Source {i}]: {res['title']}\n"
                f"URL: {res['url']}\n"
                f"Content: {res['snippet']}\n"
            )
        return "\n".join(context_parts)

web_search_engine = WebSearchEngine()
