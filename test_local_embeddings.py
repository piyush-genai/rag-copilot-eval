# PURPOSE: Test local embeddings to verify sentence-transformers works
# USAGE: python test_local_embeddings.py

import sys
import os

# Add rag-copilot-eval to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "rag-copilot-eval"))

from ingestion.embedder import embed_chunks

# Test chunks with technical runbook-style text
test_chunks = [
    {
        "text": "PostgreSQL database is experiencing high CPU usage. Check pg_stat_activity for long-running queries.",
        "chunk_id": "test_001"
    },
    {
        "text": "To restart the Nginx service, run: sudo systemctl restart nginx. Verify status with systemctl status nginx.",
        "chunk_id": "test_002"
    },
    {
        "text": "Redis memory usage exceeds 80%. Consider increasing maxmemory or enabling eviction policy.",
        "chunk_id": "test_003"
    }
]

print("Testing local embeddings (sentence-transformers)...")
print(f"USE_BEDROCK={os.getenv('USE_BEDROCK', 'false')}\n")

try:
    result = embed_chunks(test_chunks)
    
    print("✅ SUCCESS!\n")
    print(f"Embedded {len(result)} chunks:")
    
    for chunk in result:
        embedding = chunk.get("embedding")
        if embedding:
            print(f"  • {chunk['chunk_id']}: {len(embedding)}-dimensional vector")
            print(f"    First 5 values: {[f'{v:.4f}' for v in embedding[:5]]}")
        else:
            print(f"  ❌ {chunk['chunk_id']}: No embedding generated")
    
    # Verify all embeddings are 384-dimensional (local model)
    dims = [len(c.get("embedding", [])) for c in result]
    if all(d == 384 for d in dims):
        print("\n✅ All embeddings are 384-dimensional (correct for local model)")
    else:
        print(f"\n⚠️  Warning: Unexpected dimensions: {dims}")

except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
