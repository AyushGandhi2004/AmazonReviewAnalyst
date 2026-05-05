"""ChromaDB semantic query logic for RAG retrieval."""

import logging

from pipeline.embeddings import _get_chroma_client, _load_model, get_collection_name

logger = logging.getLogger(__name__)

# Fixed queries run against every product's review collection (from spec)
RAG_QUERIES = [
    "what do customers complain about most",
    "what do customers love and praise",
    "what specific product improvements do customers suggest",
    "what are the most common reasons for low ratings",
]


def query_reviews(run_id: str, asin: str, top_k: int = 10) -> dict[str, list[str]]:
    """Run all 4 semantic queries against a product's ChromaDB collection.

    Embeds each query with the same SentenceTransformer model used during
    storage, then retrieves the top_k most similar review chunks per query.

    Args:
        run_id: Run identifier used to locate the correct ChromaDB collection.
        asin: ASIN of the product whose reviews are being queried.
        top_k: Number of chunks to retrieve per query (default 10).

    Returns:
        A dict mapping each query string to a list of relevant review chunk texts.
        Example:
            {
                "what do customers complain about most": ["chunk1", "chunk2", ...],
                ...
            }

    Raises:
        RuntimeError: If the ChromaDB collection does not exist or the query fails.
    """
    collection_name = get_collection_name(run_id, asin)

    try:
        client = _get_chroma_client()
        collection = client.get_collection(name=collection_name)
    except Exception as exc:
        raise RuntimeError(
            f"ChromaDB collection '{collection_name}' not found for ASIN {asin}. "
            f"Ensure embed_and_store_reviews was called first. Error: {exc}"
        ) from exc

    # Clamp top_k to the actual number of stored documents
    doc_count = collection.count()
    effective_k = min(top_k, doc_count)
    if effective_k == 0:
        logger.warning("Collection '%s' is empty, returning no results.", collection_name)
        return {q: [] for q in RAG_QUERIES}

    model = _load_model()
    query_embeddings = model.encode(RAG_QUERIES, normalize_embeddings=True, show_progress_bar=False)

    logger.info(
        "Querying collection '%s' (%d docs) with %d queries (top_k=%d)",
        collection_name, doc_count, len(RAG_QUERIES), effective_k,
    )

    try:
        results = collection.query(
            query_embeddings=[emb.tolist() for emb in query_embeddings],
            n_results=effective_k,
            include=["documents"],
        )
    except Exception as exc:
        raise RuntimeError(
            f"ChromaDB query failed for collection '{collection_name}': {exc}"
        ) from exc

    # results["documents"] is a list-of-lists: one inner list per query
    rag_context: dict[str, list[str]] = {}
    for idx, query in enumerate(RAG_QUERIES):
        docs = results["documents"][idx] if results["documents"] else []
        rag_context[query] = [d for d in docs if d]

    return rag_context


def format_context_for_llm(rag_context: dict[str, list[str]]) -> str:
    """Flatten the RAG results dict into a single readable string for LLM prompts.

    Groups chunks by query label so the LLM understands which theme each
    excerpt relates to.

    Args:
        rag_context: Output of query_reviews().

    Returns:
        A multi-section string ready to be injected into an LLM prompt.
    """
    sections: list[str] = []
    for query, chunks in rag_context.items():
        if not chunks:
            continue
        label = query.upper()
        body = "\n".join(f"- {chunk.strip()}" for chunk in chunks)
        sections.append(f"[{label}]\n{body}")
    return "\n\n".join(sections)
