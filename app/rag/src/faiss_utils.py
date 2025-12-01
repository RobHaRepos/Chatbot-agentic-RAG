import uuid
import os
import logging
from typing import Callable
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from .constants import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    METADATA_SOURCE,
    METADATA_DOCUMENT_ID,
    METADATA_CHUNK_ID,
    METADATA_CHUNK_INDEX,
    FAISS_INDEX_FILE,
    FAISS_PKL_FILE,
    DOCUMENT_NOT_FOUND,
    SUPPORTED_FILE_EXTENSIONS,
)
from .database import Document
from . import schemas, crud

logger = logging.getLogger("retriever_service")

# ============= Index Cache =============
loaded_stores: dict[int, FAISS] = {}

# ============= Index Management =============
def get_store_index(store_id: int, index_path: str, embeddings) -> FAISS | None:
    """Load FAISS index for a given store ID, with caching. Returns None if index doesn't exist yet."""
    if store_id not in loaded_stores:
        index_file = os.path.join(index_path, FAISS_INDEX_FILE)
        if not os.path.exists(index_file):
            logger.debug(f"No index file exists yet for store {store_id}")
            return None
        logger.info(f"Loading FAISS index for store {store_id} from {index_path}")
        loaded_stores[store_id] = FAISS.load_local(
            index_path, embeddings, allow_dangerous_deserialization=True
        )
    return loaded_stores[store_id]

def invalidate_store_index(store_id: int) -> None:
    """Invalidate cached FAISS index for a given store ID."""
    if store_id in loaded_stores:
        loaded_stores.pop(store_id)
        logger.info(f"Invalidated cached FAISS index for store {store_id}")


def save_and_invalidate_index(index: FAISS, store_path: str, store_id: int) -> None:
    """Save FAISS index to disk and invalidate cache."""
    index.save_local(store_path)
    invalidate_store_index(store_id)


def get_store_or_404(db: Session, store_id: int):
    """Validate store exists and return it, or raise 404 HTTPException."""
    from .constants import STORE_NOT_FOUND
    store = crud.get_store(db, store_id)
    if not store:
        logger.info(f"Store {store_id} not found")
        raise HTTPException(status_code=404, detail=STORE_NOT_FOUND)
    return store


def remove_index_files(index_path: str) -> None:
    """Remove FAISS index files from disk."""
    index_file = os.path.join(index_path, FAISS_INDEX_FILE)
    pkl_file = os.path.join(index_path, FAISS_PKL_FILE)

    if os.path.exists(index_file):
        os.remove(index_file)
    if os.path.exists(pkl_file):
        os.remove(pkl_file)

# ============= Metadata Utilities =============
def create_chunk_metadata(filename: str, doc_id: int, chunk_index: int) -> dict:
    """Create standardized chunk metadata dictionary."""
    return {
        METADATA_SOURCE: filename,
        METADATA_DOCUMENT_ID: doc_id,
        METADATA_CHUNK_ID: str(uuid.uuid4()),
        METADATA_CHUNK_INDEX: chunk_index,
    }

# ============= Chunk Filtering =============
def filter_and_collect_chunks(
    index: FAISS | None, filter_fn: Callable, transform_fn: Callable | None = None
) -> tuple[list[str], list[dict]]:
    """Function to filter chunks from FAISS index and optionally transform metadata."""
    chunks = []
    metadatas = []

    if index is not None:
        all_docs = index.docstore._dict  # type: ignore[attr-defined]
        for _, doc_obj in all_docs.items():
            if filter_fn(doc_obj):
                if transform_fn:
                    transform_fn(doc_obj)
                chunks.append(doc_obj.page_content)
                metadatas.append(doc_obj.metadata)

    return chunks, metadatas

# ============= Index Rebuilding =============
def rebuild_index_with_new_content(
    index: FAISS | None, doc_id: int, new_content: str, filename: str, embeddings
) -> tuple[FAISS, int]:
    """Rebuild FAISS index with new content for a document. Returns (new_index, chunk_count)."""
    chunks_to_keep, metadatas_to_keep = filter_and_collect_chunks(
        index, lambda doc_obj: doc_obj.metadata.get(METADATA_DOCUMENT_ID) != doc_id
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    new_chunks = text_splitter.split_text(new_content)

    new_metadatas = [
        create_chunk_metadata(filename, doc_id, i) for i in range(len(new_chunks))
    ]

    all_chunks = chunks_to_keep + new_chunks
    all_metadatas = metadatas_to_keep + new_metadatas
    new_index = FAISS.from_texts(all_chunks, embeddings, metadatas=all_metadatas)

    return new_index, len(new_chunks)

def update_index_filenames(index: FAISS, doc_id: int, new_filename: str, embeddings) -> FAISS:
    """Update filename metadata in FAISS index for a document. Returns new index."""

    def update_source(doc_obj):
        if doc_obj.metadata.get(METADATA_DOCUMENT_ID) == doc_id:
            doc_obj.metadata[METADATA_SOURCE] = new_filename

    chunks, metadatas = filter_and_collect_chunks(
        index, lambda doc_obj: True, transform_fn=update_source 
    )

    return FAISS.from_texts(chunks, embeddings, metadatas=metadatas)

# ============= Document Validation =============
def validate_document_ownership(doc, doc_id: int, store_id: int) -> None:
    """Validate document exists and belongs to specified store. Raises HTTPException if invalid."""
    if not doc:
        logger.info(f"Document {doc_id} not found")
        raise HTTPException(status_code=404, detail=DOCUMENT_NOT_FOUND)
    if doc.store_id != store_id:  # type: ignore[comparison-overlap]
        logger.info(f"Document {doc_id} does not belong to store {store_id}")
        raise HTTPException(status_code=404, detail=DOCUMENT_NOT_FOUND)

# ============= File Upload Utilities =============
def validate_upload_file(file: UploadFile) -> None:
    """Validate uploaded file format. Raises HTTPException if invalid."""
    if not file.filename or not file.filename.endswith(SUPPORTED_FILE_EXTENSIONS):
        logger.info(f"Rejected file {file.filename}: unsupported type")
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(SUPPORTED_FILE_EXTENSIONS)} files are supported. Got: {file.filename}",
        )

async def read_and_decode_file(file: UploadFile) -> tuple[bytes, str]:
    """Read and decode file content. Returns (content_bytes, text). Raises HTTPException on error."""
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        logger.info(f"Failed to decode {file.filename}: not a valid UTF-8 text file")
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename} is not a valid UTF-8 text file",
        )

    if not text.strip():
        logger.info(f"Rejected file {file.filename}: empty content")
        raise HTTPException(
            status_code=400, detail=f"File {file.filename} is empty"
        )

    return content, text

def process_file_into_chunks(
    file: UploadFile,
    text: str,
    content: bytes,
    store_id: int,
    text_splitter: RecursiveCharacterTextSplitter,
    db: Session,
) -> tuple[list[str], list[dict], Document]:
    """Process file into chunks and create document record. Returns (chunks, metadatas, doc)."""
    chunks = text_splitter.split_text(text)
    logger.info(
        f"Split {file.filename} into {len(chunks)} chunks. "
        f"First chunk length: {len(chunks[0]) if chunks else 0}, "
        f"Last chunk length: {len(chunks[-1]) if chunks else 0}"
    )
    logger.debug(f"First 100 chars of each chunk: {[chunk[:100] for chunk in chunks[:3]]}")

    doc = crud.create_document(
        db,
        schemas.DocumentCreate(
            store_id=store_id,
            filename=str(file.filename),
            file_type=file.content_type,
            file_size=len(content),
            chunk_count=len(chunks),
        ),
    )

    metadatas = [create_chunk_metadata(str(file.filename), doc.id, i) for i in range(len(chunks))]  # type: ignore[arg-type]

    logger.info(f"Prepared {len(chunks)} chunks from {file.filename}")
    return chunks, metadatas, doc
