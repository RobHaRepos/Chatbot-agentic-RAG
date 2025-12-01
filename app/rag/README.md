# Retriever Service

FastAPI-based vector retrieval service using FAISS for semantic search. Supports multiple vector stores, document management, and configurable chunking strategies.

## Features

- **Multi-Store Support**: Create and manage multiple FAISS vector stores with different embedding models
- **Document Management**: Upload, update, and delete documents with automatic chunking
- **Semantic Search**: Sentence-transformer embeddings for similarity search
- **Chunk Tracking**: Metadata-based chunk identification and retrieval
- **SQLite Database**: Persistent storage for store/document metadata
- **Configurable Chunking**: Adjustable chunk size and overlap (defaults: 4000/800 chars)

## Architecture

**Modular Design:**
- `retriever.py` - FastAPI endpoints and application lifecycle
- `constants.py` - Configuration constants and environment variables
- `faiss_utils.py` - FAISS operations, validation, file processing
- `crud.py` - Database CRUD operations
- `database.py` - SQLAlchemy models and schemas
- `embeddings.py` - HuggingFace embedding model initialization

## API Endpoints

### Vector Stores
- `GET /stores` - List all vector stores
- `POST /stores` - Create new store: `{"name": "...", "embedding_model_id": 1}`
- `GET /stores/{store_id}` - Get store details
- `PATCH /stores/{store_id}` - Update store name
- `DELETE /stores/{store_id}` - Delete store and all documents

### Documents
- `GET /stores/{store_id}/documents` - List documents in store
- `POST /stores/{store_id}/upload` - Upload files (`.txt`, `.md`)
- `GET /stores/{store_id}/documents/{doc_id}` - Get document with full content
- `PATCH /stores/{store_id}/documents/{doc_id}` - Update filename/content
- `DELETE /stores/{store_id}/documents/{doc_id}` - Delete document and chunks

### Retrieval
- `POST /stores/{store_id}/retrieve` - Semantic search: `{"query": "...", "k": 5}`
- `POST /stores/retrieve_string` - Legacy endpoint returning concatenated text

### Metadata
- `GET /embedding-models` - List available embedding models
- `GET /health` - Health check

## Configuration

**Environment Variables:**
```bash
# Embedding Configuration
MODEL_NAME_EMBEDDING=sentence-transformers/all-MiniLM-L6-v2
PATH_TO_FAISS_INDEX=./data/stores/default_index_phones  # Default store path

# Chunking Strategy
CHUNK_SIZE=4000           # Characters per chunk
CHUNK_OVERLAP=800         # Character overlap between chunks

# Service URLs
LOGGER_SERVICE_URL=http://logger_service:8004/logs

# Database
DATABASE_URL=sqlite:///./vector_store.db  # Auto-created
```

## Quick Start

**Docker (Recommended):**
```bash
docker compose up -d retriever
curl http://localhost:8001/health
```

**Local Development:**
```bash
cd app/rag
pip install -r requirements-retriever.txt
uvicorn src.retriever:app --host 0.0.0.0 --port 8001
```

## Usage Examples

**Create Vector Store:**
```bash
curl -X POST http://localhost:8001/stores \
  -H "Content-Type: application/json" \
  -d '{"name": "My Documents", "embedding_model_id": 1}'
```

**Upload Document:**
```bash
curl -X POST http://localhost:8001/stores/1/upload \
  -F "files=@document.txt"
```

**Search Documents:**
```bash
curl -X POST http://localhost:8001/stores/1/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "k": 3}'
```

**Response:**
```json
{
  "chunks": [
    {
      "content": "Machine learning is...",
      "score": 0.85,
      "metadata": {
        "source": "document.txt",
        "document_id": 1,
        "chunk_id": "uuid...",
        "chunk_index": 0
      }
    }
  ],
  "store_id": 1,
  "store_name": "My Documents"
}
```

## Data Storage

**Directory Structure:**
```
data/stores/
├── default_index_phones/    # Default store (ID 1)
│   ├── index.faiss
│   └── index.pkl
├── store_2/                  # Custom stores
│   ├── index.faiss
│   └── index.pkl
vector_store.db               # SQLite metadata
```

## Dependencies

- **FastAPI** - API framework
- **FAISS** - Vector similarity search
- **LangChain** - Document processing and text splitting
- **HuggingFace Transformers** - Sentence embeddings
- **SQLAlchemy** - ORM and database management
- **Pydantic** - Request/response validation
