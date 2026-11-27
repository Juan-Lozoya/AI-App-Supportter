import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "")
KB_ID = os.getenv("KB_ID", "")
KB_DATA_SOURCE_ID = os.getenv("KB_DATA_SOURCE_ID", "")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")
BEDROCK_FAST_MODEL_ID = os.getenv("BEDROCK_FAST_MODEL_ID", "")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_FILES = int(os.getenv("MAX_FILES", "10"))
MAX_PASTED_CHARS = int(os.getenv("MAX_PASTED_CHARS", "200000"))
ANALYSES_TABLE = os.getenv("ANALYSES_TABLE", "corpactions-analyses")

RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.35"))
MAX_LLM_INPUT_CHARS = int(os.getenv("MAX_LLM_INPUT_CHARS", "120000"))

CORS_ORIGINS = [
  origin.strip()
  for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
  if origin.strip()
]