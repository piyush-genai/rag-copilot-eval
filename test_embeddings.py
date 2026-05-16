# PURPOSE: Quick test to verify Bedrock Titan Embeddings V2 is working
# USAGE: python test_embeddings.py

import os
import sys

# Add the rag-copilot-eval directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "rag-copilot-eval"))

from ingestion.embedder import embed_chunks

# Test with a small batch of technical runbook-style text
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

print("Testing Bedrock Titan Embeddings V2...")
print(f"Region: {os.getenv('AWS_REGION', 'us-east-1')}")
print(f"Model: {os.getenv('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v2:0')}")
print(f"\nEmbedding {len(test_chunks)} test chunks...\n")

try:
    result = embed_chunks(test_chunks)
    
    print("✅ SUCCESS!")
    print(f"\nEmbedded {len(result)} chunks")
    
    for chunk in result:
        embedding = chunk.get("embedding")
        if embedding:
            print(f"  • {chunk['chunk_id']}: {len(embedding)}-dimensional vector")
            print(f"    First 5 values: {embedding[:5]}")
        else:
            print(f"  ❌ {chunk['chunk_id']}: No embedding generated")
    
    # Verify embedding dimensions
    if all(len(c.get("embedding", [])) == 1536 for c in result):
        print("\n✅ All embeddings are 1536-dimensional (correct for Titan V2)")
    else:
        print("\n⚠️  Warning: Some embeddings have incorrect dimensions")

except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
