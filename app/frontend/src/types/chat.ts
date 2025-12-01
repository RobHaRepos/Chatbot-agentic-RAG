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

/**
 * FIXED: Proper discriminated union for API responses
 * Backend should be consistent, but we handle variations defensively
 */
export type ChatResponseResult =
  | { type: 'string'; value: string }
  | { type: 'object'; answer: string; metadata?: unknown }
  | { type: 'object'; text: string; metadata?: unknown };

export interface ChatResponse {
  result: string | {
    answer?: string | object;
    text?: string;
    [key: string]: unknown;
  };
}

/**
 * Extract text from ChatResponse regardless of structure
 * CRITICAL: This normalizes inconsistent backend responses
 */
export function extractResponseText(response: ChatResponse): string {
  const { result } = response;
  
  // String response (most common)
  if (typeof result === 'string') {
    return result;
  }
  
  // Object response with answer field
  if (typeof result === 'object' && result !== null) {
    if ('answer' in result && result.answer !== undefined) {
      return typeof result.answer === 'object'
        ? JSON.stringify(result.answer, null, 2)
        : String(result.answer);
    }
    
    // Object response with text field
    if ('text' in result && result.text !== undefined) {
      return String(result.text);
    }
    
    // Fallback: stringify entire object
    return JSON.stringify(result, null, 2);
  }
  
  // Ultimate fallback
  return 'No response received';
}
