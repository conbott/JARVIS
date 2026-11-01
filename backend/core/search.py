import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class WebSearchEngine:
    def __init__(self, max_results: int = 4):
        self.max_results = max_results

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a live web search using DuckDuckGo with zero API keys required.
        Returns a list of structured source records: title, href (url), body (snippet).
        """
        results: List[Dict[str, Any]] = []
        try:
            with DDGS() as ddgs:
                raw_results = ddgs.text(query, max_results=self.max_results)
                for item in raw_results:
                    results.append({
                        "title": item.get("title", "Untitled Source"),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", ""),
                        "source_type": "web"
                    })
            logger.info(f"DuckDuckGo search succeeded for '{query}': {len(results)} results found.")
        except Exception as e:
            logger.error(f"DuckDuckGo search error for query '{query}': {e}")
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
