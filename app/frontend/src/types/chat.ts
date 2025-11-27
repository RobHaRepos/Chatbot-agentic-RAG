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
}

export interface ChatResponse {
  result: {
    answer?: string;
    text?: string;
    action?: unknown;
  } | string;
}
