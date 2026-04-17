# PURPOSE: Lambda entry point — receives S3 ObjectCreated events and triggers the ingestion pipeline
# CALLED BY: AWS Lambda runtime on S3 event notification
# DEPENDS ON: ingestion.pdf_extractor, ingestion.chunker, ingestion.embedder, ingestion.index_writer
