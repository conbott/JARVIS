import os
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma
from config import settings
from core.embeddings import embedding_engine

logger = logging.getLogger(__name__)

def is_reference_chunk(text: str) -> bool:
    """
    Detects if a chunk primarily contains bibliographic citations / reference lists.
    Flags high density of [n] bracketed citations, 'arXiv preprint', 'et al.', and bibliography entries.
    """
    t_lower = text.lower()
    has_ref_header = bool(re.search(r'\b(references|bibliography)\b', t_lower))
    bracket_entries = len(re.findall(r'(?:^|\n)\s*\[\d+\]', text))
    if bracket_entries >= 2:
        return True
    if has_ref_header and bracket_entries >= 1:
        return True

    citations = re.findall(r'\[\d+\]', text)
    has_arxiv = "arxiv preprint" in t_lower or "arxiv:" in t_lower
    has_proc = "in proc." in t_lower or "in proceedings" in t_lower or "advances in neural" in t_lower
    et_als = len(re.findall(r'\bet\s+al\.?', text, flags=re.IGNORECASE))

    # Multiple bracketed citations with publication markers
    if len(citations) >= 3 and (has_arxiv or has_proc):
        return True
    if len(citations) >= 2 and has_arxiv and et_als >= 2:
        return True
    if has_arxiv and et_als >= 3 and ("pages " in t_lower or "vol." in t_lower):
        return True
    return False

def is_title_authors_chunk(text: str) -> bool:
    """
    Detects if a chunk is the title/author/affiliation metadata block at the start of a paper.
    """
    t_lower = text.lower()
    has_emails = len(re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)) >= 2
    has_affil = any(k in t_lower for k in ["university", "google brain", "google research", "department of", "laboratory"])
    return has_emails or (has_affil and "abstract" in t_lower[:500])

class VectorStoreManager:
    def __init__(self):
        self.persist_directory = os.path.abspath(settings.CHROMA_PERSIST_DIR)
        self.collection_name = settings.COLLECTION_NAME
        self._chroma: Optional[Chroma] = None

    @property
    def chroma(self) -> Chroma:
        if self._chroma is None:
            os.makedirs(self.persist_directory, exist_ok=True)
            logger.info(f"Connecting to ChromaDB at: {self.persist_directory}")
            self._chroma = Chroma(
                collection_name=self.collection_name,
                embedding_function=embedding_engine.client,
                persist_directory=self.persist_directory,
            )
        return self._chroma

    def add_documents(self, documents: List[Document]) -> int:
        """
        Adds split document chunks into local ChromaDB.
        """
        if not documents:
            return 0
        self.chroma.add_documents(documents)
        logger.info(f"Added {len(documents)} chunks to local ChromaDB collection '{self.collection_name}'.")
        return len(documents)

    def search_with_scores(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Performs similarity search with relevance scores.
        Returns list of (Document, score) tuples.
        """
        try:
            return self.chroma.similarity_search_with_relevance_scores(query, k=k)
        except Exception as e:
            logger.warning(f"Error during similarity search: {e}")
            # Fallback to standard similarity search if relevance scores fail
            docs = self.chroma.similarity_search(query, k=k)
            return [(d, 0.7) for d in docs]

    def get_spread_chunks(self, limit: int = 8) -> List[Tuple[Document, float]]:
        """
        Retrieves up to `limit` chunks spread evenly across the indexed documents.
        - Skips chunks that look like a reference list (many [n] citations, arXiv preprint, et al. density)
        - Always includes the first content chunk after title/authors (abstract)
        - Always includes the last non-reference chunk if present
        - Fills the rest evenly across the corpus in page order
        Returns list of (Document, score) where score is 1.0 (indicating full-corpus synthesis).
        """
        try:
            collection = self.chroma._collection
            data = collection.get(include=["documents", "metadatas"])
            raw_docs = data.get("documents", [])
            metas = data.get("metadatas", [])
            if not raw_docs:
                return []

            items = []
            for i, (text, meta) in enumerate(zip(raw_docs, metas)):
                m = meta or {}
                page = m.get("page")
                try:
                    page_num = int(page) if page is not None else 0
                except (ValueError, TypeError):
                    page_num = 0
                source_name = str(m.get("source", ""))
                items.append((source_name, page_num, i, text, m))

            # Sort by source name, then page number, then original order
            items.sort(key=lambda x: (x[0], x[1], x[2]))

            # Filter out chunks that look like a reference list
            content_items = [it for it in items if not is_reference_chunk(it[3])]
            if not content_items:
                content_items = items  # Fallback if all chunks were flagged

            total_content = len(content_items)
            if total_content <= limit:
                selected_items = content_items
            else:
                # Find first content chunk after title/authors (abstract)
                first_content_idx = 0
                if total_content > 1 and is_title_authors_chunk(content_items[0][3]):
                    first_content_idx = 1

                # Last non-reference chunk
                last_content_idx = total_content - 1

                middle_count = limit - 2
                pool_indices = list(range(first_content_idx + 1, last_content_idx))
                if len(pool_indices) <= middle_count:
                    chosen_pool = pool_indices
                else:
                    step = (len(pool_indices) - 1) / float(middle_count - 1) if middle_count > 1 else 0
                    chosen_pool = [pool_indices[int(round(k * step))] for k in range(middle_count)]
                    chosen_pool = sorted(list(dict.fromkeys(chosen_pool)))

                final_indices = [first_content_idx] + chosen_pool + [last_content_idx]
                final_indices = sorted(list(dict.fromkeys(final_indices)))
                selected_items = [content_items[idx] for idx in final_indices]

            result: List[Tuple[Document, float]] = []
            for it in selected_items:
                _, _, _, text, m = it
                doc = Document(page_content=text, metadata=m)
                result.append((doc, 1.0))
            return result
        except Exception as e:
            logger.error(f"Error retrieving spread chunks: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns stats about local ChromaDB and unique indexed files.
        """
        try:
            collection = self.chroma._collection
            count = collection.count()
            
            # Fetch all metadata to get list of unique file names
            results = collection.get(include=["metadatas"])
            filenames = set()
            if results and "metadatas" in results and results["metadatas"]:
                for meta in results["metadatas"]:
                    if meta and "source" in meta:
                        filenames.add(os.path.basename(meta["source"]))

            return {
                "total_chunks": count,
                "document_count": len(filenames),
                "documents": sorted(list(filenames)),
                "storage_type": "local_chroma",
                "collection": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error fetching Chroma stats: {e}")
            return {
                "total_chunks": 0,
                "document_count": 0,
                "documents": [],
                "error": str(e)
            }

    def clear_documents(self) -> bool:
        """
        Deletes all entries from the local ChromaDB collection.
        """
        try:
            self.chroma.delete_collection()
            self._chroma = None
            return True
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {e}")
            return False

    def sync_to_pinecone(self, api_key: Optional[str] = None, index_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Reads local vectors from ChromaDB and replicates them into Pinecone cloud.
        """
        key = api_key or settings.PINECONE_API_KEY
        idx = index_name or settings.PINECONE_INDEX_NAME

        if not key:
            return {
                "success": False,
                "message": "Pinecone API key is required. Please set PINECONE_API_KEY in .env or pass it via request."
            }

        try:
            from pinecone import Pinecone
            from langchain_pinecone import PineconeVectorStore

            pc = Pinecone(api_key=key)
            existing_indexes = [i.name for i in pc.list_indexes()]

            if idx not in existing_indexes:
                return {
                    "success": False,
                    "message": f"Index '{idx}' not found in your Pinecone account. Existing indexes: {existing_indexes}"
                }

            # Retrieve all documents from local Chroma
            collection = self.chroma._collection
            data = collection.get(include=["documents", "metadatas"])
            raw_docs = data.get("documents", [])
            metas = data.get("metadatas", [])

            if not raw_docs:
                return {
                    "success": False,
                    "message": "Local ChromaDB has 0 documents to sync. Upload documents first."
                }

            docs_to_sync: List[Document] = []
            for text, meta in zip(raw_docs, metas):
                docs_to_sync.append(Document(page_content=text, metadata=meta or {}))

            # Push to Pinecone
            logger.info(f"Syncing {len(docs_to_sync)} vectors to Pinecone index '{idx}'...")
            PineconeVectorStore.from_documents(
                documents=docs_to_sync,
                embedding=embedding_engine.client,
                index_name=idx,
                pinecone_api_key=key
            )

            return {
                "success": True,
                "synced_count": len(docs_to_sync),
                "index_name": idx,
                "message": f"Successfully synced {len(docs_to_sync)} vectors to Pinecone index '{idx}'."
            }

        except Exception as e:
            logger.error(f"Pinecone sync error: {e}")
            return {
                "success": False,
                "message": f"Pinecone sync failed: {str(e)}"
            }

vector_store_manager = VectorStoreManager()
