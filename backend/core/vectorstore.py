import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma
from config import settings
from core.embeddings import embedding_engine

logger = logging.getLogger(__name__)

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
