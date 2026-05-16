# PURPOSE: Test FAISS retrieval with sample runbook questions
# CALLED BY: Manual execution to verify search works
# DEPENDS ON: retrieval.faiss_fallback, ingestion.embedder

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval.faiss_fallback import FAISSVectorStore
from ingestion.embedder import embed_chunks

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ─── TEST QUERIES ─────────────────────────────────────────────────────────────

# Real questions someone might ask about technical runbooks
TEST_QUERIES = [
    "How do I restart PostgreSQL database?",
    "What to do when Redis memory is high?",
    "How to check Nginx service status?",
    "Steps to troubleshoot high CPU usage",
    "How to rotate database credentials?"
]


# ─── MAIN TEST ────────────────────────────────────────────────────────────────

def main():
    """
    Load FAISS index and test retrieval with sample queries.
    """
    logger.info("="*70)
    logger.info("FAISS RETRIEVAL TEST")
    logger.info("="*70)
    
    # Load the FAISS index
    logger.info("\n1. Loading FAISS index...")
    vector_store = FAISSVectorStore()
    
    try:
        vector_store.load()
        logger.info(f"   ✓ Loaded {vector_store.total_vectors} vectors")
    except RuntimeError as e:
        logger.error(f"   ✗ Failed to load index: {e}")
        logger.error("\n   Run 'python scripts/build_faiss_index.py' first!")
        sys.exit(1)
    
    # Test each query
    logger.info("\n2. Testing retrieval with sample queries...\n")
    
    for i, query in enumerate(TEST_QUERIES, 1):
        logger.info(f"\n{'─'*70}")
        logger.info(f"Query {i}: {query}")
        logger.info('─'*70)
        
        # Convert query to embedding
        # Why wrap in list: embed_chunks expects list of dicts
        query_chunks = [{"text": query}]
        embedded_query = embed_chunks(query_chunks)
        query_embedding = embedded_query[0]["embedding"]
        
        # Search FAISS
        # Why k=3: show top 3 results per query (enough to verify relevance)
        results = vector_store.search(query_embedding, k=3)
        
        if not results:
            logger.info("   ⚠️  No results found")
            continue
        
        # Display results
        for j, result in enumerate(results, 1):
            logger.info(f"\n   Result {j} (score: {result.score:.4f})")
            logger.info(f"   Source: {result.source_runbook}")
            logger.info(f"   Section: {result.section_name}")
            
            # Show first 150 chars of chunk text
            # Why 150: enough to verify relevance without cluttering output
            preview = result.chunk_text[:150].replace('\n', ' ')
            if len(result.chunk_text) > 150:
                preview += "..."
            logger.info(f"   Text: {preview}")
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("✅ RETRIEVAL TEST COMPLETE")
    logger.info("="*70)
    logger.info("\nNext steps:")
    logger.info("  • If results look relevant → retrieval is working!")
    logger.info("  • If results are random → check embedding quality")
    logger.info("  • Ready to add generation (Day 6) or reranking (Day 7)")


if __name__ == "__main__":
    main()
