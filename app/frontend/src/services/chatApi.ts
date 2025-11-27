import api from './api';
import { ChatRequest, ChatResponse } from '@/types/chat';

export const sendMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await api.post<ChatResponse>('', request);
  return response.data;
};
