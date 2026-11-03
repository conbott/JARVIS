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
        self._chroma: Optional[Chroma] = None
        self._pinecone_index: Optional[Any] = None

    @property
    def vector_backend(self) -> str:
        return settings.VECTOR_BACKEND

    @property
    def chroma_collection_name(self) -> str:
        return embedding_engine.collection_name

    @property
    def chroma(self) -> Chroma:
        coll_name = self.chroma_collection_name
        if self._chroma is None or getattr(self._chroma, "_collection_name", None) != coll_name:
            os.makedirs(self.persist_directory, exist_ok=True)
            logger.info(f"Connecting to ChromaDB collection '{coll_name}' at: {self.persist_directory}")
            try:
                self._chroma = Chroma(
                    collection_name=coll_name,
                    embedding_function=embedding_engine.client,
                    persist_directory=self.persist_directory,
                )
                self._chroma._collection_name = coll_name
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {e}")
                raise ValueError(f"Vector database initialization error: {e}")
        return self._chroma

    def _get_pinecone_index(self):
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set. Please provide it in .env to use Pinecone vector backend.")
        if self._pinecone_index is None:
            from pinecone import Pinecone, ServerlessSpec
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            # 1. Detect embedding dimension by embedding one test string
            try:
                test_vec = embedding_engine.client.embed_query("dimension_check")
                dim = len(test_vec)
                logger.info(f"Detected embedding dimension {dim} for model '{settings.EMBEDDING_MODEL}' ({settings.EMBEDDING_PROVIDER})")
            except Exception as e:
                logger.error(f"Failed to detect embedding dimension: {e}")
                raise ValueError(f"Could not determine embedding dimension using model '{settings.EMBEDDING_MODEL}': {e}")

            # 2. Check if index exists or create it
            existing_indexes = [i.name for i in pc.list_indexes()]
            if settings.PINECONE_INDEX_NAME not in existing_indexes:
                logger.info(f"Pinecone index '{settings.PINECONE_INDEX_NAME}' not found. Creating index with dimension {dim} and cosine metric...")
                pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=dim,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )
                import time
                for _ in range(60):
                    desc = pc.describe_index(settings.PINECONE_INDEX_NAME)
                    status = desc.status
                    is_ready = status.get("ready", False) if isinstance(status, dict) else getattr(status, "ready", False)
                    if is_ready:
                        logger.info(f"Pinecone index '{settings.PINECONE_INDEX_NAME}' is ready.")
                        break
                    time.sleep(1)
            else:
                # 3. Verify dimension matches
                desc = pc.describe_index(settings.PINECONE_INDEX_NAME)
                existing_dim = getattr(desc, "dimension", None)
                if existing_dim is not None and existing_dim != dim:
                    raise ValueError(
                        f"Pinecone dimension mismatch: existing index '{settings.PINECONE_INDEX_NAME}' has dimension {existing_dim}, "
                        f"but active embedding model '{settings.EMBEDDING_MODEL}' ({settings.EMBEDDING_PROVIDER}) produces {dim}-dimensional vectors. "
                        f"Please specify a PINECONE_INDEX_NAME with {dim} dimensions or change the EMBEDDING_MODEL."
                    )

            self._pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)
        return self._pinecone_index

    def add_documents(self, documents: List[Document], session_id: Optional[str] = None) -> int:
        """
        Adds split document chunks into either local ChromaDB or Pinecone cloud.
        Assigns deterministic IDs (<doc_id>-<chunk_index>) and attaches source/page/chunk_index metadata.
        """
        if not documents:
            return 0

        # Attach deterministic IDs and metadata
        deterministic_ids = []
        for idx, doc in enumerate(documents):
            source_file = os.path.basename(doc.metadata.get("source", "document"))
            clean_source = re.sub(r'[^a-zA-Z0-9_-]', '_', source_file)
            chunk_id = f"{clean_source}-{idx}"
            deterministic_ids.append(chunk_id)
            doc.metadata["chunk_index"] = idx
            doc.metadata["doc_id"] = clean_source
            if "source" not in doc.metadata:
                doc.metadata["source"] = source_file
            if "page" not in doc.metadata:
                doc.metadata["page"] = 1

        if self.vector_backend == "pinecone":
            namespace = session_id or "default"
            logger.info(f"Adding {len(documents)} chunks directly to Pinecone index '{settings.PINECONE_INDEX_NAME}' (namespace='{namespace}')")
            try:
                from langchain_pinecone import PineconeVectorStore
                pc_index = self._get_pinecone_index()
                vector_store = PineconeVectorStore(
                    index=pc_index,
                    embedding=embedding_engine.client,
                    namespace=namespace
                )
                vector_store.add_documents(documents=documents, ids=deterministic_ids, namespace=namespace)
                return len(documents)
            except Exception as e:
                err_msg = str(e)
                if "dimension" in err_msg.lower():
                    raise ValueError(f"Pinecone dimension mismatch: {err_msg}")
                logger.error(f"Pinecone add_documents error: {e}")
                raise

        # Default local ChromaDB
        try:
            self.chroma.add_documents(documents=documents, ids=deterministic_ids)
            logger.info(f"Added {len(documents)} chunks to ChromaDB collection '{self.chroma_collection_name}'.")
            return len(documents)
        except Exception as e:
            err_msg = str(e)
            if "dimension" in err_msg.lower():
                raise ValueError(
                    f"Vector dimension mismatch in ChromaDB collection '{self.chroma_collection_name}': {err_msg}. "
                    "Clear documents or switch EMBEDDING_MODEL."
                )
            logger.error(f"ChromaDB add_documents error: {e}")
            raise

    def search_with_scores(self, query: str, k: int = 4, session_id: Optional[str] = None) -> List[Tuple[Document, float]]:
        """
        Performs similarity search with relevance scores [0.0, 1.0].
        """
        if self.vector_backend == "pinecone":
            namespace = session_id or "default"
            try:
                from langchain_pinecone import PineconeVectorStore
                pc_index = self._get_pinecone_index()
                vector_store = PineconeVectorStore(
                    index=pc_index,
                    embedding=embedding_engine.client,
                    namespace=namespace
                )
                return vector_store.similarity_search_with_relevance_scores(query, k=k, namespace=namespace)
            except Exception as e:
                logger.warning(f"Error during Pinecone similarity search: {e}")
                return []

        try:
            return self.chroma.similarity_search_with_relevance_scores(query, k=k)
        except Exception as e:
            logger.warning(f"Error during ChromaDB similarity search: {e}")
            try:
                docs = self.chroma.similarity_search(query, k=k)
                return [(d, 0.7) for d in docs]
            except Exception as inner_err:
                logger.error(f"Failed fallback similarity search: {inner_err}")
                return []

    def get_spread_chunks(self, limit: int = 8, session_id: Optional[str] = None) -> List[Tuple[Document, float]]:
        """
        Retrieves up to `limit` chunks spread evenly across the indexed documents.
        """
        if self.vector_backend == "pinecone":
            namespace = session_id or "default"
            try:
                pc_index = self._get_pinecone_index()
                # Query with an overview embedding vector to fetch top candidates across namespace
                overview_vec = embedding_engine.client.embed_query("overview of document structure, key themes, and conclusions")
                stats = pc_index.describe_index_stats()
                total_count = getattr(stats, "total_vector_count", 100) or 100
                query_res = pc_index.query(
                    vector=overview_vec,
                    top_k=min(100, max(20, total_count)),
                    include_metadata=True,
                    namespace=namespace
                )
                matches = getattr(query_res, "matches", []) or []
                if not matches:
                    return []

                items = []
                for i, m in enumerate(matches):
                    meta = m.metadata or {}
                    text = meta.get("text") or meta.get("page_content") or ""
                    page = meta.get("page", 1)
                    try:
                        page_num = int(page)
                    except (ValueError, TypeError):
                        page_num = 1
                    source_name = str(meta.get("source", ""))
                    chunk_idx = meta.get("chunk_index", i)
                    items.append((source_name, page_num, chunk_idx, text, meta))

                items.sort(key=lambda x: (x[0], x[1], x[2]))
                content_items = [it for it in items if not is_reference_chunk(it[3])]
                if not content_items:
                    content_items = items

                total_content = len(content_items)
                if total_content <= limit:
                    selected_items = content_items
                else:
                    first_idx = 0
                    if total_content > 1 and is_title_authors_chunk(content_items[0][3]):
                        first_idx = 1
                    last_idx = total_content - 1
                    middle_count = limit - 2
                    pool_indices = list(range(first_idx + 1, last_idx))
                    if len(pool_indices) <= middle_count:
                        chosen_pool = pool_indices
                    else:
                        step = (len(pool_indices) - 1) / float(middle_count - 1) if middle_count > 1 else 0
                        chosen_pool = [pool_indices[int(round(k * step))] for k in range(middle_count)]
                        chosen_pool = sorted(list(dict.fromkeys(chosen_pool)))
                    final_indices = sorted(list(dict.fromkeys([first_idx] + chosen_pool + [last_idx])))
                    selected_items = [content_items[idx] for idx in final_indices]

                return [(Document(page_content=it[3], metadata=it[4]), 1.0) for it in selected_items]
            except Exception as e:
                logger.error(f"Error retrieving Pinecone spread chunks: {e}")
                return []

        # Local ChromaDB spread retrieval
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
                chunk_idx = m.get("chunk_index", i)
                items.append((source_name, page_num, chunk_idx, text, m))

            items.sort(key=lambda x: (x[0], x[1], x[2]))
            content_items = [it for it in items if not is_reference_chunk(it[3])]
            if not content_items:
                content_items = items

            total_content = len(content_items)
            if total_content <= limit:
                selected_items = content_items
            else:
                first_content_idx = 0
                if total_content > 1 and is_title_authors_chunk(content_items[0][3]):
                    first_content_idx = 1
                last_content_idx = total_content - 1
                middle_count = limit - 2
                pool_indices = list(range(first_content_idx + 1, last_content_idx))
                if len(pool_indices) <= middle_count:
                    chosen_pool = pool_indices
                else:
                    step = (len(pool_indices) - 1) / float(middle_count - 1) if middle_count > 1 else 0
                    chosen_pool = [pool_indices[int(round(k * step))] for k in range(middle_count)]
                    chosen_pool = sorted(list(dict.fromkeys(chosen_pool)))

                final_indices = sorted(list(dict.fromkeys([first_content_idx] + chosen_pool + [last_content_idx])))
                selected_items = [content_items[idx] for idx in final_indices]

            return [(Document(page_content=it[3], metadata=it[4]), 1.0) for it in selected_items]
        except Exception as e:
            logger.error(f"Error retrieving ChromaDB spread chunks: {e}")
            return []

    def get_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns stats about active vector store (ChromaDB or Pinecone).
        """
        if self.vector_backend == "pinecone":
            namespace = session_id or "default"
            try:
                pc_index = self._get_pinecone_index()
                desc = pc_index.describe_index_stats()
                ns_data = desc.namespaces.get(namespace) if hasattr(desc, "namespaces") and desc.namespaces else None
                vec_count = ns_data.vector_count if ns_data else (desc.total_vector_count or 0)
                return {
                    "total_chunks": vec_count,
                    "document_count": 1 if vec_count > 0 else 0,
                    "documents": [f"Pinecone Namespace: {namespace}"] if vec_count > 0 else [],
                    "storage_type": "pinecone",
                    "collection": settings.PINECONE_INDEX_NAME,
                    "namespace": namespace
                }
            except Exception as e:
                logger.error(f"Error fetching Pinecone stats: {e}")
                return {
                    "total_chunks": 0,
                    "document_count": 0,
                    "documents": [],
                    "storage_type": "pinecone",
                    "error": str(e)
                }

        try:
            collection = self.chroma._collection
            count = collection.count()
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
                "collection": self.chroma_collection_name
            }
        except Exception as e:
            logger.error(f"Error fetching Chroma stats: {e}")
            return {
                "total_chunks": 0,
                "document_count": 0,
                "documents": [],
                "storage_type": "local_chroma",
                "error": str(e)
            }

    def clear_documents(self, session_id: Optional[str] = None) -> bool:
        """
        Clears documents from either ChromaDB or Pinecone namespace.
        """
        if self.vector_backend == "pinecone":
            namespace = session_id or "default"
            try:
                pc_index = self._get_pinecone_index()
                pc_index.delete(delete_all=True, namespace=namespace)
                logger.info(f"Cleared Pinecone vectors in namespace '{namespace}'.")
                return True
            except Exception as e:
                logger.error(f"Error clearing Pinecone namespace '{namespace}': {e}")
                return False

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
