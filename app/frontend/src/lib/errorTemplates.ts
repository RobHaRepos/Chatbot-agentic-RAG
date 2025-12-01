/**
 * Standardized error context templates
 * CRITICAL: Eliminates inconsistent handleError usage across 15+ components
 * 
 * Usage:
 * handleError(error, ...ERROR_TEMPLATES.STORE_CREATE(storeName));
 */

export const ERROR_TEMPLATES = {
  // Vector Store Errors
  STORE_CREATE: (name: string): [string, { title: string; context: Record<string, string> }] => [
    'Failed to create store',
    {
      title: 'Creation Failed',
      context: { name },
    },
  ],

  STORE_DELETE: (id: number, name: string): [string, { title: string; context: Record<string, string | number> }] => [
    'Failed to delete store',
    {
      title: 'Deletion Failed',
      context: { storeId: id, storeName: name },
    },
  ],

  STORE_UPDATE: (id: number, name: string): [string, { title: string; context: Record<string, string | number> }] => [
    'Failed to update store status',
    {
      title: 'Update Failed',
      context: { storeId: id, storeName: name },
    },
  ],

  STORE_FETCH: (): [string, { title: string }] => [
    'Failed to load stores',
    {
      title: 'Load Failed',
    },
  ],

  // Document Errors
  DOCUMENT_UPLOAD: (storeId: number, fileCount: number): [string, { title: string; context: Record<string, number> }] => [
    'Failed to upload documents',
    {
      title: 'Upload Failed',
      context: { storeId, fileCount },
    },
  ],

  // Retrieval Errors
  RETRIEVAL_QUERY: (storeId: number, query: string): [string, { title: string; context: Record<string, string | number> }] => [
    'Failed to retrieve documents',
    {
      title: 'Retrieval Error',
      context: { storeId, query },
    },
  ],

  // Chat Errors
  CHAT_SEND: (storeId: number, question: string): [string, { title: string; context: Record<string, string | number> }] => [
    'Failed to get response',
    {
      title: 'Chat Error',
      context: { storeId, question },
    },
  ],

  // TTS Errors
  TTS_GENERATE: (text: string, voice: string, speed: number): [string, { title: string; context: Record<string, string | number> }] => [
    'Failed to generate speech',
    {
      title: 'TTS Error',
      context: { textLength: text.length, voice, speed },
    },
  ],
} as const;
