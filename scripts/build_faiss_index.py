# PURPOSE: Build FAISS index from runbook markdown files
# CALLED BY: Manual execution during development
# DEPENDS ON: ingestion.chunker, ingestion.embedder, retrieval.faiss_fallback

import os
import sys
import pickle
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.chunker import chunk_section
from ingestion.embedder import embed_chunks
from retrieval.faiss_fallback import FAISSVectorStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ─── CONFIGURATION ────────────────────────────────────────────────────────────

# Path to runbooks directory
RUNBOOKS_DIR = Path(__file__).parent.parent / "data" / "runbooks"

# Output paths
OUTPUT_DIR = Path(__file__).parent.parent / "data"
CHUNKS_FILE = OUTPUT_DIR / "chunks_with_embeddings.pkl"
INDEX_FILE = OUTPUT_DIR / "faiss_index.bin"
METADATA_FILE = OUTPUT_DIR / "chunk_metadata.pkl"


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────

def main():
    """
    Build FAISS index from markdown runbooks.
    
    Steps:
    1. Read all .md files from data/runbooks/
    2. Chunk each file using semantic chunking
    3. Embed all chunks using local model
    4. Build FAISS index from embeddings
    5. Save index + metadata to disk
    """
    logger.info("Starting FAISS index build...")
    
    # Step 1: Find all markdown files
    md_files = list(RUNBOOKS_DIR.glob("*.md"))
    logger.info(f"Found {len(md_files)} markdown files in {RUNBOOKS_DIR}")
    
    if not md_files:
        logger.error(f"No markdown files found in {RUNBOOKS_DIR}")
        sys.exit(1)
    
    # Step 2: Read and chunk all files
    all_chunks = []
    for md_file in md_files:
        logger.info(f"Processing {md_file.name}...")
        
        # Read file content
        # Why utf-8: markdown files are text, utf-8 handles special characters
        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {md_file.name}: {e}")
            continue
        
        # Chunk the text
        # Why chunk_section: treats entire markdown as one section for simplicity
        # In production, you'd detect sections first (Overview, Steps, etc.)
        chunks = chunk_section(
            section_text=text,
            metadata={
                "source_runbook": md_file.name,
                "section_name": "full_document",
                "service_name": "unknown",  # Could parse from filename
                "team_owner": "unknown",
                "severity_level": "unknown",
                "page_num": 1
            }
        )
        
        logger.info(f"  → {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    logger.info(f"\nTotal chunks: {len(all_chunks)}")
    
    if not all_chunks:
        logger.error("No chunks generated. Check your markdown files.")
        sys.exit(1)
    
    # Step 3: Embed all chunks
    logger.info("\nEmbedding chunks (this may take a few minutes)...")
    embedded_chunks = embed_chunks(all_chunks)
    
    # Step 4: Build FAISS index
    logger.info("\nBuilding FAISS index...")
    vector_store = FAISSVectorStore()
    vector_store.add_chunks(embedded_chunks)
    
    # Step 5: Save everything to disk
    logger.info("\nSaving artifacts...")
    
    # Save FAISS index and metadata
    vector_store.save(str(INDEX_FILE), str(METADATA_FILE))
    logger.info(f"  ✓ Saved FAISS index to {INDEX_FILE}")
    logger.info(f"  ✓ Saved metadata to {METADATA_FILE}")
    
    # Save chunks with embeddings for reference
    # Why save chunks: useful for debugging and analysis
    with open(CHUNKS_FILE, "wb") as f:
        pickle.dump(embedded_chunks, f)
    logger.info(f"  ✓ Saved chunks to {CHUNKS_FILE}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✅ FAISS index build complete!")
    logger.info(f"   • {len(embedded_chunks)} chunks indexed")
    logger.info(f"   • {len(md_files)} markdown files processed")
    logger.info(f"   • Index dimension: {len(embedded_chunks[0]['embedding'])}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
