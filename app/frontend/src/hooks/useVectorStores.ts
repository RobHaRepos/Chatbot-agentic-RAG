import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  fetchStores, 
  fetchStore, 
  createStore, 
  updateStore, 
  deleteStore,
  fetchDocuments,
  fetchDocument,
  updateDocument,
  deleteDocument,
  uploadDocuments,
  fetchEmbeddingModels,
  retrieveChunks
} from '@/services/api';
import type { 
  VectorStore,
  VectorStoreCreate, 
  VectorStoreUpdate,
  Document,
  DocumentUpdate,
  RetrievalRequest 
} from '@/types/vectorStore';

// Query keys
export const storeKeys = {
  all: ['stores'] as const,
  detail: (id: number) => ['stores', id] as const,
  embeddingModels: ['embedding-models'] as const,
  documents: (storeId: number) => ['stores', storeId, 'documents'] as const,
  document: (storeId: number, docId: number) => ['stores', storeId, 'documents', docId] as const,
};

// ======= Queries =======
export function useStores() {
  return useQuery({
    queryKey: storeKeys.all,
    queryFn: fetchStores,
  });
}

export function useStore(id: number) {
  return useQuery({
    queryKey: storeKeys.detail(id),
    queryFn: () => fetchStore(id),
    enabled: !!id,
  });
}

export function useEmbeddingModels() {
  return useQuery({
    queryKey: storeKeys.embeddingModels,
    queryFn: fetchEmbeddingModels,
  });
}

// ======= Mutations =======
export function useCreateStore() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: VectorStoreCreate) => createStore(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: storeKeys.all });
    },
  });
}

interface UpdateStoreParams {
  id: number;
  data: VectorStoreUpdate;
}

export function useUpdateStore() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: UpdateStoreParams) => updateStore(id, data),
    onSuccess: (_result: VectorStore, { id }: UpdateStoreParams) => {
      queryClient.invalidateQueries({ queryKey: storeKeys.all });
      queryClient.invalidateQueries({ queryKey: storeKeys.detail(id) });
    },
  });
}

export function useDeleteStore() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => deleteStore(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: storeKeys.all });
    },
  });
}

interface UploadDocumentsParams {
  storeId: number;
  files: File[];
  onProgress?: (progress: number) => void;
}

export function useUploadDocuments() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ storeId, files, onProgress }: UploadDocumentsParams) => 
      uploadDocuments(storeId, files, onProgress),
    onSuccess: (_result: Document[], { storeId }: UploadDocumentsParams) => {
      // Invalidate store details to update document count
      queryClient.invalidateQueries({ queryKey: storeKeys.detail(storeId) });
      queryClient.invalidateQueries({ queryKey: storeKeys.all });
    },
  });
}

export function useRetrieveChunks() {
  return useMutation({
    mutationFn: ({ storeId, request }: { storeId: number; request: RetrievalRequest }) =>
      retrieveChunks(storeId, request),
  });
}

// ======= Document Queries =======
export function useDocuments(storeId: number) {
  return useQuery({
    queryKey: storeKeys.documents(storeId),
    queryFn: () => fetchDocuments(storeId),
    enabled: !!storeId,
  });
}

export function useDocument(storeId: number, docId: number) {
  return useQuery({
    queryKey: storeKeys.document(storeId, docId),
    queryFn: () => fetchDocument(storeId, docId),
    enabled: !!storeId && !!docId,
  });
}

// ======= Document Mutations =======
interface UpdateDocumentParams {
  storeId: number;
  docId: number;
  data: DocumentUpdate;
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ storeId, docId, data }: UpdateDocumentParams) => 
      updateDocument(storeId, docId, data),
    onSuccess: (_result: Document, { storeId, docId }: UpdateDocumentParams) => {
      // Invalidate document lists and details
      queryClient.invalidateQueries({ queryKey: storeKeys.documents(storeId) });
      queryClient.invalidateQueries({ queryKey: storeKeys.document(storeId, docId) });
      queryClient.invalidateQueries({ queryKey: storeKeys.detail(storeId) });
      queryClient.invalidateQueries({ queryKey: storeKeys.all });
    },
  });
}

interface DeleteDocumentParams {
  storeId: number;
  docId: number;
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ storeId, docId }: DeleteDocumentParams) => 
      deleteDocument(storeId, docId),
    onSuccess: (_result: void, { storeId }: DeleteDocumentParams) => {
      // Invalidate document lists and store details
      queryClient.invalidateQueries({ queryKey: storeKeys.documents(storeId) });
      queryClient.invalidateQueries({ queryKey: storeKeys.detail(storeId) });
      queryClient.invalidateQueries({ queryKey: storeKeys.all });
    },
  });
}
