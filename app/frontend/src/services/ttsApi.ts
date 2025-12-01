import axios from 'axios';
import { getTTSUrl } from '@/lib/utils';

// Create a dedicated axios instance for TTS API
const ttsApi = axios.create({
  baseURL: getTTSUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface TTSRequest {
  readonly text: string;
  readonly voice?: string;
  readonly speed?: number;
}

export const generateSpeech = async (
  text: string,
  voice?: string,
  speed?: number
): Promise<Blob> => {
  const request: TTSRequest = {
    text,
    ...(voice && { voice }),
    ...(speed !== undefined && { speed }),
  };

  const response = await ttsApi.post('', request, {
    responseType: 'blob',
  });
  return response.data;
};
