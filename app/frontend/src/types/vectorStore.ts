// ======= Embedding Models =======
export interface EmbeddingModel {
  id: number;
  name: string;
  display_name: string | null;
  dimension: number;
  description: string | null;
  is_available: boolean;
}

// ======= Vector Stores =======
export interface VectorStore {
  id: number;
  name: string;
  description: string | null;
  embedding_model: EmbeddingModel;
  document_count: number;
  chunk_count: number;
  is_active: boolean;
}

export interface VectorStoreCreate {
  name: string;
  description?: string;
  embedding_model_id: number;
}

export interface VectorStoreUpdate {
  name: string;
  description?: string;
  is_active?: boolean;
}

// ======= Documents =======
export interface Document {
  id: number;
  filename: string;
  file_type: string | null;
  file_size: number | null;
  chunk_count: number;
}

export interface DocumentUpdate {
  filename?: string;
  content?: string;
}

export interface DocumentWithContent extends Document {
  content: string;
}

// ======= Retrieval =======
export interface RetrievalRequest {
  query: string;
  k?: number;
}

export interface RetrievedChunk {
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface RetrievalResponse {
  chunks: RetrievedChunk[];
  store_id: number;
  store_name: string;
}
