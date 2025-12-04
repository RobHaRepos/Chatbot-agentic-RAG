from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

#======== Schemas for Retriever Service =======
class EmbeddingModelResponse(BaseModel):
    """Response schema for embedding model details. Defines API output structure."""
    id : int
    name: str
    display_name: Optional[str]
    dimension: int
    description: Optional[str]
    is_available: bool
    
class VectorStoreCreate(BaseModel):
    """Request schema and validation of incoming JSON for creating a vector store."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model_id: int
    
class VectorStoreUpdate(BaseModel):
    """Request schema and validation of incoming JSON for updating a vector store."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
class VectorStoreResponse(BaseModel):
    """Response schema for vector store details. Defines API output structure."""
    id: int
    name: str
    description: Optional[str]
    embedding_model: EmbeddingModelResponse
    document_count: int
    chunk_count: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
        
class DocumentResponse(BaseModel):
    """Response schema for document details. Defines API output structure."""
    id: int
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    chunk_count: int
    
    model_config = ConfigDict(from_attributes=True)

class RetrievalRequest(BaseModel):
    """Request schema for document retrieval. Validates incoming JSON."""
    query: str
    k: int = Field(default=5, ge=1, le=20)
    store_id: Optional[int] = None

class RetrievedChunk(BaseModel):
    """Schema for a retrieved text chunk with content, score, and metadata."""
    content: str
    score: float
    metadata: dict

class RetrievalResponse(BaseModel):
    """Response schema for retrieval results. Contains list of retrieved chunks and store info."""
    chunks: List[RetrievedChunk]
    store_id: int
    store_name: str
    
class DocumentCreate(BaseModel):
    """Request schema for creating a document. Validates incoming JSON."""
    store_id: int
    filename: str
    file_type: Optional[str] = None
    file_size: int
    chunk_count: int

class DocumentUpdate(BaseModel):
    """Request schema for updating a document. Validates incoming JSON."""
    filename: Optional[str] = Field(None, min_length=1, max_length=512)
    content: Optional[str] = Field(None, min_length=1)
    
class DocumentWithContent(BaseModel):
    """Response schema for document with full content."""
    id: int
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    chunk_count: int
    content: str
    
    model_config = ConfigDict(from_attributes=True)
    
# ======= Prompt Schemas =======
class TemplateType(str, Enum):
    """Enum for template types to ensure consistency."""
    RETRIEVE_OR_RESPOND = "retrieve_or_respond"
    GENERATE_ANSWER = "generate_answer"
    
class MessageBlock(BaseModel):
    """Schema for a single message block in a prompt template."""
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str = Field(..., min_length=1)
    
class TemplateCreateIn(BaseModel):
    """Request schema for creating a prompt template."""
    name: str = Field(..., min_length=1, max_length=255)
    template_type: TemplateType
    store_id: int
    messages: List[MessageBlock] = Field(..., min_length=1)

class TemplateUpdateIn(BaseModel):
    """Request schema for updating a prompt template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    messages: Optional[List[MessageBlock]] = Field(None, min_length=1)
    is_active: Optional[bool] = None

class TemplateResponse(BaseModel):
    """Response schema for prompt template details."""
    id: int
    name: str
    template_type: str
    store_id: int
    messages: List[MessageBlock]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
    