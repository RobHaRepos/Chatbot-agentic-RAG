import axios from 'axios';
import { getApiBaseUrl } from '@/lib/utils';
import type { 
  VectorStore, 
  VectorStoreCreate, 
  VectorStoreUpdate, 
  EmbeddingModel,
  Document,
  DocumentUpdate,
  DocumentWithContent,
  RetrievalRequest,
  RetrievalResponse 
} from '@/types/vectorStore';
import type { ChatRequest, ChatResponse } from '@/types/chat';
import type { Template, TemplateCreate, TemplateUpdate } from '@/types/template';

// Base URL for chat/workflow API
const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Base URL for retriever API (vector stores)
const retrieverApi = axios.create({
  baseURL: '/api/retriever',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ======= Vector Stores =======
export const fetchStores = async (): Promise<VectorStore[]> => {
  const response = await retrieverApi.get<VectorStore[]>('/stores');
  return response.data;
};

export const fetchStore = async (id: number): Promise<VectorStore> => {
  const response = await retrieverApi.get<VectorStore>(`/stores/${id}`);
  return response.data;
};

export const createStore = async (data: VectorStoreCreate): Promise<VectorStore> => {
  const response = await retrieverApi.post<VectorStore>('/stores', data);
  return response.data;
};

export const updateStore = async (id: number, data: VectorStoreUpdate): Promise<VectorStore> => {
  const response = await retrieverApi.patch<VectorStore>(`/stores/${id}`, data);
  return response.data;
};

export const deleteStore = async (id: number): Promise<void> => {
  await retrieverApi.delete(`/stores/${id}`);
};

// ======= Documents =======
export const fetchDocuments = async (storeId: number): Promise<Document[]> => {
  const response = await retrieverApi.get<Document[]>(`/stores/${storeId}/documents`);
  return response.data;
};

export const fetchDocument = async (storeId: number, docId: number): Promise<DocumentWithContent> => {
  const response = await retrieverApi.get<DocumentWithContent>(`/stores/${storeId}/documents/${docId}`);
  return response.data;
};

export const updateDocument = async (
  storeId: number,
  docId: number,
  data: DocumentUpdate
): Promise<Document> => {
  const response = await retrieverApi.patch<Document>(`/stores/${storeId}/documents/${docId}`, data);
  return response.data;
};

export const deleteDocument = async (storeId: number, docId: number): Promise<void> => {
  await retrieverApi.delete(`/stores/${storeId}/documents/${docId}`);
};

export const uploadDocuments = async (
  storeId: number, 
  files: File[],
  onProgress?: (progress: number) => void
): Promise<Document[]> => {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  
  const response = await retrieverApi.post<Document[]>(`/stores/${storeId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return response.data;
};

// ======= Embedding Models =======
export const fetchEmbeddingModels = async (): Promise<EmbeddingModel[]> => {
  const response = await retrieverApi.get<EmbeddingModel[]>('/embedding-models');
  return response.data;
};

// ======= Retrieval =======
export const retrieveFromStore = async (
  storeId: number, 
  request: RetrievalRequest
): Promise<RetrievalResponse> => {
  const response = await retrieverApi.post<RetrievalResponse>(
    `/stores/${storeId}/retrieve`, 
    request
  );
  return response.data;
};

// Alias for React Query hook compatibility
export const retrieveChunks = retrieveFromStore;

// ======= Chat =======
export const sendMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('', request);
  return response.data;
};

// ======= Templates =======
export const fetchTemplates = async (storeId?: number): Promise<Template[]> => {
  const params = storeId ? { store_id: storeId } : {};
  const response = await retrieverApi.get<Template[]>('/templates', { params });
  return response.data;
};

export const fetchTemplate = async (templateId: number): Promise<Template> => {
  const response = await retrieverApi.get<Template>(`/templates/${templateId}`);
  return response.data;
};

export const createTemplate = async (data: TemplateCreate): Promise<Template> => {
  const response = await retrieverApi.post<Template>('/templates', data);
  return response.data;
};

export const updateTemplate = async (
  templateId: number,
  data: TemplateUpdate
): Promise<Template> => {
  const response = await retrieverApi.patch<Template>(`/templates/${templateId}`, data);
  return response.data;
};

export const deleteTemplate = async (templateId: number): Promise<void> => {
  await retrieverApi.delete(`/templates/${templateId}`);
};

export default api;
