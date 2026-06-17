import structlog
import uuid
from typing import List
import os
from app.config import get_settings

logger = structlog.get_logger(__name__)

# ─── Module-level singletons ──────────────────────────────────────────────
# Loaded ONCE when this module is first imported, never re-per-request.
_embedding_model = None
_chroma_client = None
_embedding_fn = None


def get_embedding_model():
    """Lazy singleton -- model loads once, reused for all subsequent calls."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        settings = get_settings()
        logger.info("loading_embedding_model", model=settings.embedding_model)
        _embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("embedding_model_loaded")
    return _embedding_model


def get_embedding_function():
    """Returns a singleton ChromaDB-compatible embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = SentenceTransformerEmbeddingFunction()
    return _embedding_fn


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


class SentenceTransformerEmbeddingFunction:
    """
    ChromaDB-compatible embedding function.
    Uses the shared singleton model -- never instantiates its own model.
    """
    def __call__(self, input: List[str]) -> List[List[float]]:
        model = get_embedding_model()
        embeddings = model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()


# ─── Public API ────────────────────────────────────────────────────────────

async def create_kb_collection(collection_name: str) -> str:
    """
    Creates a ChromaDB collection with the given name.
    Uses SentenceTransformer embedding function.
    """
    try:
        chroma_client = get_chroma_client()
        embedding_function = get_embedding_function()

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
        embedding_function = get_embedding_function()

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
        embedding_function = get_embedding_function()

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
) -> str:
    """
    Retrieve context from the knowledge base collection.
    """
    try:
        settings = get_settings()
        if top_k is None:
            top_k = settings.rag_top_k

        chroma_client = get_chroma_client()
        embedding_function = get_embedding_function()

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
