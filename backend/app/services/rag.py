import structlog
import uuid
from typing import List, Optional
import os
import requests
from sqlalchemy.orm import Session
from app.config import get_settings
logger = structlog.get_logger(__name__)

# ─── Module-level singletons ──────────────────────────────────────────────
_chroma_client = None


def resolve_user_gemini_key(db: Session, user_id: int) -> Optional[str]:
    """Helper to query the user's active Gemini API key from the database,
    falling back to settings.google_api_key.
    """
    from app.models.user_api_key import UserApiKey
    from app.utils.encryption import decrypt_key
    from app.config import settings

    key_row = (
        db.query(UserApiKey)
        .filter(
            UserApiKey.user_id == user_id,
            UserApiKey.provider == "gemini",
            UserApiKey.is_active == True,
        )
        .first()
    )
    if key_row:
        try:
            return decrypt_key(key_row.api_key)
        except Exception:
            pass

    if settings.google_api_key:
        return settings.google_api_key

    return None


def get_embedding_function(api_key: Optional[str] = None):
    """Returns a ChromaDB-compatible Gemini API embedding function."""
    return GeminiEmbeddingFunction(api_key)


def get_chroma_client():
    """Returns a singleton ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        from chromadb import Client as ChromaClient
        from chromadb.config import Settings as ChromaSettings
        settings = get_settings()
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = ChromaClient(ChromaSettings(
            persist_directory=settings.chroma_persist_dir,
            is_persistent=True,
        ))
    return _chroma_client


class GeminiEmbeddingFunction:
    """
    ChromaDB-compatible embedding function using the Gemini API.
    Does not require PyTorch or transformers locally.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().google_api_key

    def __call__(self, input: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ValueError(
                "Gemini API key is required for RAG embeddings. "
                "Please configure a Gemini API key in your Profile or .env file."
            )
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents?key={self.api_key}"
            payload = {
                "requests": [
                    {
                        "model": "models/gemini-embedding-001",
                        "content": {"parts": [{"text": text}]},
                        "outputDimensionality": 384
                    }
                    for text in input
                ]
            }
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            embeddings = [emb["values"] for emb in data.get("embeddings", [])]
            return embeddings
        except Exception as e:
            logger.error("gemini_embedding_failed", error=str(e))
            raise RuntimeError(f"Failed to generate Gemini embeddings: {str(e)}") from e


# ─── Public API ────────────────────────────────────────────────────────────

async def create_kb_collection(collection_name: str, api_key: Optional[str] = None) -> str:
    """
    Creates a ChromaDB collection with the given name.
    Uses Gemini embedding function.
    """
    try:
        chroma_client = get_chroma_client()
        embedding_function = get_embedding_function(api_key)

        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )
        logger.info("kb_collection_created", collection_name=collection_name)
        return collection_name
    except Exception as e:
        logger.error("failed_to_create_kb_collection", error=str(e), collection_name=collection_name)
        raise


async def delete_kb_collection(collection_name: str) -> bool:
    """
    Deletes the ChromaDB collection.
    Returns True on success, False if not found.
    """
    try:
        chroma_client = get_chroma_client()

        try:
            chroma_client.delete_collection(name=collection_name)
            logger.info("kb_collection_deleted", collection_name=collection_name)
            return True
        except Exception:
            logger.warning("kb_collection_not_found_for_deletion", collection_name=collection_name)
            return False
    except Exception as e:
        logger.error("failed_to_delete_kb_collection", error=str(e), collection_name=collection_name)
        return False


async def ingest_file(
    collection_name: str,
    file_bytes: bytes,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    api_key: Optional[str] = None,
) -> int:
    """
    Ingest a file (PDF or text) into the knowledge base collection.
    """
    try:
        text = ""
        if filename.lower().endswith(".pdf"):
            import PyPDF2
            import io
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        elif filename.lower().endswith(".txt"):
            text = file_bytes.decode("utf-8")
        else:
            text = file_bytes.decode("utf-8")

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - chunk_overlap

        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]

        chroma_client = get_chroma_client()
        embedding_function = get_embedding_function(api_key)

        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

        collection.add(
            embeddings=embedding_function(chunks),
            documents=chunks,
            ids=ids,
        )

        logger.info("file_ingested", filename=filename, chunks=len(chunks))
        return len(chunks)
    except Exception as e:
        logger.error("failed_to_ingest_file", error=str(e), filename=filename)
        raise


async def ingest_text(
    collection_name: str,
    text: str,
    source: str = "manual",
    api_key: Optional[str] = None,
) -> int:
    """
    Ingest raw text into the knowledge base collection.
    """
    try:
        chunk_size = 500
        chunk_overlap = 50
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - chunk_overlap

        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]

        chroma_client = get_chroma_client()
        embedding_function = get_embedding_function(api_key)

        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

        collection.add(
            embeddings=embedding_function(chunks),
            documents=chunks,
            ids=ids,
        )

        logger.info("text_ingested", source=source, chunks=len(chunks))
        return len(chunks)
    except Exception as e:
        logger.error("failed_to_ingest_text", error=str(e), source=source)
        raise


async def retrieve_context(
    collection_name: str,
    query: str,
    top_k: int = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Retrieve context from the knowledge base collection.
    """
    try:
        settings = get_settings()
        if top_k is None:
            top_k = settings.rag_top_k

        chroma_client = get_chroma_client()
        embedding_function = get_embedding_function(api_key)

        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        documents = results.get("documents", [[]])[0]
        if not documents:
            return ""

        context = "\n---\n".join(documents)
        logger.info("context_retrieved", query=query, chunks=len(documents))
        return context
    except Exception as e:
        logger.warning("failed_to_retrieve_context", error=str(e), collection_name=collection_name)
        return ""
