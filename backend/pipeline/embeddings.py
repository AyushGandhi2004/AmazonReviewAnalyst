"""SentenceTransformer embeddings and ChromaDB storage."""

import logging
import re
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config import settings
from models import Review

logger = logging.getLogger(__name__)

# Reviews longer than this (chars) are split before embedding
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Module-level singletons — loaded once, reused across all calls
_model: Optional[SentenceTransformer] = None
_chroma_client: Optional[chromadb.PersistentClient] = None


def _load_model() -> SentenceTransformer:
    """Return the shared SentenceTransformer instance, loading it on first call.

    Downloads ~90 MB on first run; cached locally by HuggingFace Hub afterwards.
    """
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded.")
    return _model


def _get_chroma_client() -> chromadb.PersistentClient:
    """Return the shared ChromaDB PersistentClient, creating it on first call."""
    global _chroma_client
    if _chroma_client is None:
        logger.info("Opening ChromaDB at: %s", settings.chroma_persist_dir)
        _chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection_name(run_id: str, asin: str) -> str:
    """Return the ChromaDB collection name for a run/ASIN pair.

    Format: run_{run_id}_{asin} — sanitised to only alphanumeric, hyphens,
    and underscores so it passes ChromaDB's naming rules.
    """
    raw = f"run_{run_id}_{asin}".lower()
    sanitised = re.sub(r"[^a-z0-9_-]", "_", raw)
    # ChromaDB requires the name to start and end with alphanumeric
    sanitised = re.sub(r"^[^a-z0-9]+", "", sanitised)
    sanitised = re.sub(r"[^a-z0-9]+$", "", sanitised)
    return sanitised[:63]  # max 63 chars


def _chunk_text(text: str) -> list[str]:
    """Split long review text into overlapping chunks.

    Only called when text exceeds CHUNK_SIZE. Most reviews are short enough
    to store as a single document.

    Args:
        text: Raw review body text.

    Returns:
        List of text chunks with CHUNK_OVERLAP character overlap.
    """
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def embed_and_store_reviews(run_id: str, asin: str, reviews: list[Review]) -> str:
    """Embed reviews and store them in a ChromaDB collection.

    Each review (or chunk of a long review) is stored as a document with
    metadata (asin, rating, date, verified). The collection is namespaced
    by run_id so concurrent runs never collide.

    Args:
        run_id: Unique identifier for the current analysis run.
        asin: ASIN the reviews belong to.
        reviews: List of Review objects to embed and store.

    Returns:
        The ChromaDB collection name used for this product.

    Raises:
        RuntimeError: If embedding or ChromaDB persistence fails.
    """
    collection_name = get_collection_name(run_id, asin)

    valid = [r for r in reviews if r.text and r.text.strip()]
    if not valid:
        logger.warning("No non-empty reviews to embed for ASIN %s", asin)
        return collection_name

    # Build flat lists for ChromaDB bulk-add
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    for idx, review in enumerate(valid):
        meta = {
            "asin": asin,
            "rating": review.rating,
            "date": review.date or "",
            "verified": str(review.verified_purchase),
            "title": review.title or "",
        }
        chunks = _chunk_text(review.text.strip())
        for chunk_idx, chunk in enumerate(chunks):
            doc_id = f"{asin}_{idx}_{chunk_idx}"
            ids.append(doc_id)
            texts.append(chunk)
            metadatas.append(meta)

    logger.info(
        "Embedding %d document(s) for ASIN %s (from %d reviews)",
        len(texts), asin, len(valid),
    )

    try:
        model = _load_model()
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        # Convert numpy array rows to plain Python lists for ChromaDB
        embeddings_list = [emb.tolist() for emb in embeddings]
    except Exception as exc:
        raise RuntimeError(f"Embedding failed for ASIN {asin}: {exc}") from exc

    try:
        client = _get_chroma_client()
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadatas,
        )
    except Exception as exc:
        raise RuntimeError(
            f"ChromaDB storage failed for ASIN {asin} (collection {collection_name}): {exc}"
        ) from exc

    logger.info(
        "Stored %d document(s) in ChromaDB collection '%s'",
        len(texts), collection_name,
    )
    return collection_name


def delete_run_collections(run_id: str, asins: list[str]) -> None:
    """Delete all ChromaDB collections for a completed run to free disk space.

    Args:
        run_id: The run whose collections should be deleted.
        asins: All ASINs that were processed in this run.
    """
    client = _get_chroma_client()
    for asin in asins:
        name = get_collection_name(run_id, asin)
        try:
            client.delete_collection(name)
            logger.info("Deleted ChromaDB collection: %s", name)
        except Exception as exc:
            logger.warning("Could not delete collection %s: %s", name, exc)
