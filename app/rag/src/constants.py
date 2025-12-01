import os
from pathlib import Path

# ============= Environment Variables =============
LOGGER_SERVICE_URL = os.environ.get("LOGGER_SERVICE_URL", "http://localhost:8004")
PATH_TO_FAISS_INDEX = os.environ.get(
    "PATH_TO_FAISS_INDEX", 
    str(Path(__file__).resolve().parent.parent.parent.parent / "data/stores/default_index_phones")
)
MODEL_NAME_EMBEDDING = os.environ.get("MODEL_NAME_EMBEDDING", "")
DEFAULT_K = int(os.environ.get("NUMBER_OF_DOCUMENTS_TO_RETRIEVE", 10))

# ============= Chunking Configuration =============
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 4000))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 800))

# ============= Error Messages =============
STORE_NOT_FOUND = "Vector store not found"
DOCUMENT_NOT_FOUND = "Document not found"

# ============= Metadata Keys =============
METADATA_SOURCE = "source"
METADATA_DOCUMENT_ID = "document_id"
METADATA_CHUNK_ID = "chunk_id"
METADATA_CHUNK_INDEX = "chunk_index"

# ============= FAISS File Names =============
FAISS_INDEX_FILE = "index.faiss"
FAISS_PKL_FILE = "index.pkl"

# ============= Supported File Extensions =============
SUPPORTED_FILE_EXTENSIONS = ('.txt', '.md')
