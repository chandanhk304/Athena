"""
Vector Indexer — Pinecone Integration
Embeds text via Pinecone Inference API (multilingual-e5-large, 1024-dim)
and upserts vectors with rich metadata for semantic search.

Free tier: 5M tokens/month for embeddings, 100K vectors storage.
"""
import time
from pinecone import Pinecone
from . import config

_pc = None
_index = None


def _get_index():
    """Lazy-init Pinecone client and index."""
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
        _index = _pc.Index(config.PINECONE_INDEX_NAME)
    return _index


def _get_client():
    """Get Pinecone client for inference."""
    global _pc
    if _pc is None:
        _pc = Pinecone(api_key=config.PINECONE_API_KEY)
    return _pc


def _embed_text(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    """
    Generate embeddings using Pinecone Inference API.
    input_type: 'passage' for indexing, 'query' for searching.
    Returns list of embedding vectors (1024-dim each).
    """
    if not texts:
        return []

    pc = _get_client()
    # Pinecone Inference API — free 5M tokens/month
    embeddings = pc.inference.embed(
        model=config.PINECONE_EMBED_MODEL,
        inputs=texts,
        parameters={"input_type": input_type, "truncate": "END"}
    )
    return [e["values"] for e in embeddings]


def _build_text_for_entity(entity_type: str, fields: dict) -> str | None:
    """
    Build the text string to embed based on entity type.
    Returns None if there's nothing meaningful to embed.
    """
    if entity_type == "story":
        title = fields.get("title", "")
        desc = fields.get("description", "")
        status = fields.get("status", "")
        priority = fields.get("priority", "")
        key = fields.get("key", "")
        text = f"[{key}] {title}. {desc}. Status: {status}. Priority: {priority}."
        return text.strip() if title else None

    elif entity_type == "comment":
        body = fields.get("body", "")
        return body.strip() if body else None

    elif entity_type == "epic":
        title = fields.get("title", "")
        desc = fields.get("description", "")
        text = f"Epic: {title}. {desc}"
        return text.strip() if title else None

    return None


def _build_metadata(entity_type: str, fields: dict, entity_id: str) -> dict:
    """Build metadata dict for the Pinecone vector."""
    meta = {
        "entity_type": entity_type,
        "entity_id": entity_id,
    }

    # Add type-specific metadata for filtering
    if entity_type == "story":
        meta["key"] = fields.get("key", "")
        meta["title"] = fields.get("title", "")[:200]  # Pinecone metadata limit
        meta["status"] = fields.get("status", "")
        meta["priority"] = fields.get("priority", "")
        meta["epic_id"] = fields.get("epic_id", "")
        meta["sprint_id"] = fields.get("sprint_id", "")
        meta["assignee_id"] = fields.get("assignee_id", "")

    elif entity_type == "comment":
        meta["story_id"] = fields.get("story_id", "")
        meta["body_preview"] = fields.get("body", "")[:200]

    elif entity_type == "epic":
        meta["key"] = fields.get("key", "")
        meta["title"] = fields.get("title", "")[:200]
        meta["project_id"] = fields.get("project_id", "")
        meta["status"] = fields.get("status", "")

    return meta


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

# Entity types that should be embedded (text-heavy entities)
EMBEDDABLE_TYPES = {"story", "comment", "epic"}


def index_event(event: dict) -> bool:
    """
    Embed and upsert a webhook event to Pinecone.
    Only processes story, comment, and epic events (text-heavy).
    Returns True if indexed, False if skipped.
    """
    entity_type = event.get("webhookEvent", "").lower()
    if entity_type not in EMBEDDABLE_TYPES:
        return False

    fields = event.get("issue", {}).get("fields", {})
    entity_id = event.get("issue", {}).get("id", "")

    if not entity_id:
        return False

    # Merge entity_id into fields if not present
    if "id" not in fields:
        fields["id"] = entity_id

    # Build text to embed
    text = _build_text_for_entity(entity_type, fields)
    if not text:
        return False

    # Generate embedding
    try:
        vectors = _embed_text([text], input_type="passage")
        if not vectors:
            return False
    except Exception as e:
        print(f"[VectorIndexer] Embedding failed: {e}")
        return False

    # Build metadata
    metadata = _build_metadata(entity_type, fields, entity_id)

    # Upsert to Pinecone
    try:
        index = _get_index()
        index.upsert(vectors=[{
            "id": entity_id,
            "values": vectors[0],
            "metadata": metadata
        }])
        return True
    except Exception as e:
        print(f"[VectorIndexer] Upsert failed: {e}")
        return False


def index_batch(events: list[dict]) -> int:
    """
    Batch embed and upsert multiple events.
    More efficient than single calls (fewer API roundtrips).
    Returns count of successfully indexed events.
    """
    # Filter to embeddable events
    embeddable = []
    for event in events:
        entity_type = event.get("webhookEvent", "").lower()
        if entity_type not in EMBEDDABLE_TYPES:
            continue
        fields = event.get("issue", {}).get("fields", {})
        entity_id = event.get("issue", {}).get("id", "")
        if not entity_id:
            continue
        if "id" not in fields:
            fields["id"] = entity_id
        text = _build_text_for_entity(entity_type, fields)
        if text:
            embeddable.append((entity_id, entity_type, fields, text))

    if not embeddable:
        return 0

    # Batch embed (Pinecone Inference supports batch)
    texts = [item[3] for item in embeddable]
    try:
        all_vectors = _embed_text(texts, input_type="passage")
    except Exception as e:
        print(f"[VectorIndexer] Batch embedding failed: {e}")
        return 0

    # Build upsert payload
    upsert_data = []
    for i, (entity_id, entity_type, fields, _) in enumerate(embeddable):
        if i < len(all_vectors):
            metadata = _build_metadata(entity_type, fields, entity_id)
            upsert_data.append({
                "id": entity_id,
                "values": all_vectors[i],
                "metadata": metadata
            })

    # Upsert in batches of 100 (Pinecone limit)
    index = _get_index()
    indexed = 0
    for batch_start in range(0, len(upsert_data), 100):
        batch = upsert_data[batch_start:batch_start + 100]
        try:
            index.upsert(vectors=batch)
            indexed += len(batch)
        except Exception as e:
            print(f"[VectorIndexer] Batch upsert failed at {batch_start}: {e}")

    return indexed


def search_docs(text: str, k: int = 5, filter_dict: dict = None) -> list[dict]:
    """
    Agent Tool #12: Semantic similarity search on Pinecone.
    Returns top-k results with scores and metadata.
    """
    try:
        vectors = _embed_text([text], input_type="query")
        if not vectors:
            return []
    except Exception as e:
        print(f"[VectorIndexer] Query embedding failed: {e}")
        return []

    index = _get_index()
    query_params = {
        "vector": vectors[0],
        "top_k": k,
        "include_metadata": True
    }
    if filter_dict:
        query_params["filter"] = filter_dict

    try:
        results = index.query(**query_params)
        return [
            {
                "id": match["id"],
                "score": match["score"],
                "metadata": match.get("metadata", {})
            }
            for match in results.get("matches", [])
        ]
    except Exception as e:
        print(f"[VectorIndexer] Query failed: {e}")
        return []


def get_vector_count() -> int:
    """Get total vector count for metrics endpoint."""
    try:
        index = _get_index()
        stats = index.describe_index_stats()
        return stats.get("total_vector_count", 0)
    except Exception as e:
        print(f"[VectorIndexer] Stats failed: {e}")
        return 0
