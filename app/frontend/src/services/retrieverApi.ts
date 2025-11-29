import axios from 'axios';
import type {
  VectorStore,
  VectorStoreCreate,
  VectorStoreUpdate,
  EmbeddingModel,
  RetrievalRequest,
  RetrievalResponse,
} from '@/types/vectorStore';

// Retriever service runs on port 8001
const RETRIEVER_BASE_URL = '/api/retriever';

const retrieverApi = axios.create({
  baseURL: RETRIEVER_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ======= Embedding Models =======
export const getEmbeddingModels = async (): Promise<EmbeddingModel[]> => {
  const response = await retrieverApi.get<EmbeddingModel[]>('/embedding-models');
  return response.data;
};

// ======= Vector Stores CRUD =======
export const getStores = async (): Promise<VectorStore[]> => {
  const response = await retrieverApi.get<VectorStore[]>('/stores');
  return response.data;
};

export const getStore = async (storeId: number): Promise<VectorStore> => {
  const response = await retrieverApi.get<VectorStore>(`/stores/${storeId}`);
  return response.data;
};

export const createStore = async (store: VectorStoreCreate): Promise<VectorStore> => {
  const response = await retrieverApi.post<VectorStore>('/stores', store);
  return response.data;
};

export const updateStore = async (storeId: number, store: VectorStoreUpdate): Promise<VectorStore> => {
  const response = await retrieverApi.put<VectorStore>(`/stores/${storeId}`, store);
  return response.data;
};

export const deleteStore = async (storeId: number): Promise<void> => {
  await retrieverApi.delete(`/stores/${storeId}`);
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

export const retrieveAsString = async (
  storeId: number,
  request: RetrievalRequest
): Promise<{ documents: string }> => {
  const response = await retrieverApi.post<{ documents: string }>(
    '/stores/retrieve_string',
    request,
    { params: { store_id: storeId } }
  );
  return response.data;
};
