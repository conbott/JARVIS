import os
import shutil
import logging
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from config import settings
from core.vectorstore import vector_store_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])

class SyncPineconeRequest(BaseModel):
    api_key: Optional[str] = None
    index_name: Optional[str] = None

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """
    Accepts PDF, TXT, or MD documents, splits into chunks, and saves to configured vector store
    (ChromaDB or direct to Pinecone).
    Enforces MAX_UPLOAD_MB upload limits.
    """
    allowed_extensions = [".pdf", ".txt", ".md"]
    filename = file.filename or "uploaded_doc"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {allowed_extensions}"
        )

    # Check file size limit if configured
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, filename)

    total_read = 0
    try:
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 64)
                if not chunk:
                    break
                total_read += len(chunk)
                if settings.MAX_UPLOAD_MB > 0 and total_read > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_MB} MB."
                    )
                buffer.write(chunk)

        extracted_docs: List[Document] = []

        if ext == ".pdf":
            loader = PyPDFLoader(temp_path)
            raw_docs = loader.load()
            for d in raw_docs:
                if d.page_content.strip():
                    raw_page = d.metadata.get("page", 0)
                    page_num = raw_page + 1 if isinstance(raw_page, int) else 1
                    d.metadata = {
                        "source": filename,
                        "page": page_num
                    }
                    extracted_docs.append(d)
        else:
            loader = TextLoader(temp_path, encoding="utf-8")
            raw_docs = loader.load()
            for d in raw_docs:
                if d.page_content.strip():
                    d.metadata = {
                        "source": filename,
                        "page": 1
                    }
                    extracted_docs.append(d)

        if not extracted_docs:
            raise HTTPException(status_code=400, detail="Could not extract any readable text from the document.")

        # Chunk documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        split_chunks = splitter.split_documents(extracted_docs)

        # Store in vector backend (ChromaDB or Pinecone)
        added_count = vector_store_manager.add_documents(split_chunks, session_id=x_session_id)
        backend_name = "Pinecone" if vector_store_manager.vector_backend == "pinecone" else "ChromaDB"

        return {
            "success": True,
            "filename": filename,
            "chunks_added": added_count,
            "pages_parsed": len(extracted_docs),
            "vector_backend": vector_store_manager.vector_backend,
            "namespace": x_session_id if vector_store_manager.vector_backend == "pinecone" else None,
            "message": f"Successfully indexed '{filename}' into {backend_name} ({added_count} chunks)."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

@router.get("/stats")
async def get_document_stats(x_session_id: Optional[str] = Header(None, alias="X-Session-Id")):
    """
    Returns current count of chunks and list of indexed documents in active vector store.
    """
    return vector_store_manager.get_stats(session_id=x_session_id)

@router.post("/sync-pinecone")
async def sync_pinecone_endpoint(request: SyncPineconeRequest):
    """
    Synchronizes local ChromaDB vectors to Pinecone cloud index.
    """
    result = vector_store_manager.sync_to_pinecone(
        api_key=request.api_key,
        index_name=request.index_name
    )
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("message", "Sync failed"))
    return result

@router.delete("/clear")
async def clear_documents(x_session_id: Optional[str] = Header(None, alias="X-Session-Id")):
    """
    Wipes the active vector collection/namespace.
    """
    success = vector_store_manager.clear_documents(session_id=x_session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear vector store.")
    backend_name = "Pinecone namespace" if vector_store_manager.vector_backend == "pinecone" else "ChromaDB collection"
    return {"success": True, "message": f"{backend_name} cleared successfully."}
