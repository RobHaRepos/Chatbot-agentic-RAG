export interface VectorStore {
  id: string;
  name: string;
  type: 'faiss' | 'pgvector';
  documentCount: number;
  embeddingModel: string;
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
}

export interface CreateStoreRequest {
  name: string;
  type: 'faiss' | 'pgvector';
  embeddingModel: string;
  files: File[];
}

export interface Document {
  id: string;
  filename: string;
  addedAt: Date;
  size: number;
}
