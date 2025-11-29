export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isLoading?: boolean;
}

export interface ChatRequest {
  question: string;
  k?: number;
  store_id?: number;  // Vector store to query
}

export interface ChatResponse {
  result: {
    answer?: string;
    text?: string;
    action?: unknown;
  } | string;
}
