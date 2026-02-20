import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# ── Init Pinecone ─────────────────────────────────────────────────────────────
def get_pinecone_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "json")
    return pc.Index(index_name)


# ── Get all namespaces ────────────────────────────────────────────────────────
def get_all_namespaces() -> list[str]:
    """Fetch all namespace names from the Pinecone index."""
    try:
        index = get_pinecone_index()
        stats = index.describe_index_stats()
        namespaces = list(stats.namespaces.keys())
        return sorted(namespaces)
    except Exception as e:
        print(f"Error fetching namespaces: {e}")
        return []


# ── Embed query ───────────────────────────────────────────────────────────────
def embed_query(query: str, openai_client) -> list[float]:
    """Embed the user's query using text-embedding-3-small."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding


# ── Query Pinecone across all namespaces ──────────────────────────────────────
def query_pinecone(query: str, top_k: int = 3, openai_client=None) -> list[dict]:
    """
    Query all namespaces in the Pinecone index and return the top matches.
    Returns a flat list of match dicts with 'namespace' added.
    """
    if openai_client is None:
        raise ValueError("openai_client is required")

    index = get_pinecone_index()
    query_vector = embed_query(query, openai_client)

    # Get all namespaces
    namespaces = get_all_namespaces()

    all_matches = []

    for ns in namespaces:
        try:
            result = index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=ns,
                include_metadata=True,
            )
            for match in result.matches:
                all_matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "namespace": ns,
                })
        except Exception as e:
            print(f"Error querying namespace '{ns}': {e}")
            continue

    # Sort all matches by score descending, return top results
    all_matches.sort(key=lambda x: x["score"], reverse=True)
    return all_matches[:top_k * 4]  # return top matches across all namespaces


# ── Query a single namespace ──────────────────────────────────────────────────
def query_namespace(query: str, namespace: str, top_k: int = 5, openai_client=None) -> list[dict]:
    """Query a specific namespace only."""
    if openai_client is None:
        raise ValueError("openai_client is required")

    index = get_pinecone_index()
    query_vector = embed_query(query, openai_client)

    result = index.query(
        vector=query_vector,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )

    return [
        {
            "id": m.id,
            "score": m.score,
            "metadata": m.metadata,
            "namespace": namespace,
        }
        for m in result.matches
    ]