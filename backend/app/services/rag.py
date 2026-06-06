import structlog
import uuid
from typing import List
import os
from app.config import get_settings

logger = structlog.get_logger()

# We will import the necessary modules inside the functions to avoid loading them if not used,
# but note that we have added the dependencies in requirements.txt.

async def create_kb_collection(collection_name: str) -> str:
    """
    Creates a ChromaDB collection with the given name.
    Uses SentenceTransformer embedding function.
    """
    try:
        from chromadb import Client
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        # Ensure the persist directory exists
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)

        # Initialize ChromaDB client with persistence
        chroma_client = Client(Settings(
            persist_directory=settings.chroma_persist_dir,
            is_persistent=True
        ))

        # Create embedding function
        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        # Create or get the collection
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        logger.info("kb_collection_created", collection_name=collection_name)
        return collection_name
    except Exception as e:
        logger.error("failed_to_create_kb_collection", error=str(e), collection_name=collection_name)
        raise

# We define a helper class for the embedding function to match ChromaDB's expected interface
class SentenceTransformerEmbeddingFunction:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        # Generate embeddings for a list of texts
        embeddings = self.model.encode(input)
        return embeddings.tolist()

async def delete_kb_collection(collection_name: str) -> bool:
    """
    Deletes the ChromaDB collection.
    Returns True on success, False if not found.
    """
    try:
        from chromadb import Client
        from chromadb.config import Settings

        settings = get_settings()
        chroma_client = Client(Settings(
            persist_directory=settings.chroma_persist_dir,
            is_persistent=True
        ))

        # Try to delete the collection
        try:
            chroma_client.delete_collection(name=collection_name)
            logger.info("kb_collection_deleted", collection_name=collection_name)
            return True
        except Exception:
            # Collection might not exist
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
    chunk_overlap: int = 50
) -> int:
    """
    Ingest a file (PDF or text) into the knowledge base collection.
    """
    try:
        # Extract text from the file
        text = ""
        if filename.lower().endswith('.pdf'):
            import PyPDF2
            import io
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        elif filename.lower().endswith('.txt'):
            text = file_bytes.decode('utf-8')
        else:
            # Assume it's text
            text = file_bytes.decode('utf-8')

        # Split text into chunks
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - chunk_overlap

        # Generate unique IDs for each chunk
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]

        # Add to ChromaDB
        from chromadb import Client
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        chroma_client = Client(Settings(
            persist_directory=settings.chroma_persist_dir,
            is_persistent=True
        ))

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        # Get the collection
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=embedding_function
        )

        # Add the chunks
        collection.add(
            embeddings=embedding_function(chunks),
            documents=chunks,
            ids=ids
        )

        logger.info("file_ingested", filename=filename, chunks=len(chunks))
        return len(chunks)
    except Exception as e:
        logger.error("failed_to_ingest_file", error=str(e), filename=filename)
        raise

async def ingest_text(
    collection_name: str,
    text: str,
    source: str = "manual"
) -> int:
    """
    Ingest raw text into the knowledge base collection.
    """
    try:
        # Use the same chunking logic as ingest_file
        chunk_size = 500
        chunk_overlap = 50
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - chunk_overlap

        # Generate unique IDs for each chunk
        ids = [str(uuid.uuid4()) for _ in range(len(chunks))]

        # Add to ChromaDB
        from chromadb import Client
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        chroma_client = Client(Settings(
            persist_directory=settings.chroma_persist_dir,
            is_persistent=True
        ))

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        # Get the collection
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=embedding_function
        )

        # Add the chunks
        collection.add(
            embeddings=embedding_function(chunks),
            documents=chunks,
            ids=ids
        )

        logger.info("text_ingested", source=source, chunks=len(chunks))
        return len(chunks)
    except Exception as e:
        logger.error("failed_to_ingest_text", error=str(e), source=source)
        raise

async def retrieve_context(
    collection_name: str,
    query: str,
    top_k: int = None
) -> str:
    """
    Retrieve context from the knowledge base collection.
    """
    try:
        settings = get_settings()
        if top_k is None:
            top_k = settings.rag_top_k

        from chromadb import Client
        from chromadb.config import Settings
        from sentence_transformers import SentenceTransformer

        chroma_client = Client(Settings(
            persist_directory=settings.chroma_persist_dir,
            is_persistent=True
        ))

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        # Get the collection
        collection = chroma_client.get_collection(
            name=collection_name,
            embedding_function=embedding_function
        )

        # Query the collection
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Extract the documents
        documents = results.get('documents', [[]])[0]
        if not documents:
            return ""

        # Join the documents with separator
        context = "\n---\n".join(documents)
        logger.info("context_retrieved", query=query, chunks=len(documents))
        return context
    except Exception as e:
        # If the collection doesn't exist, we return empty string
        logger.warning("failed_to_retrieve_context", error=str(e), collection_name=collection_name)
        return ""