# PURPOSE: Splits detected sections into token-bounded chunks with configurable overlap
# CALLED BY: ingestion.lambda_handler
# DEPENDS ON: ingestion.section_detector, tiktoken or sentence-transformers tokenizer
