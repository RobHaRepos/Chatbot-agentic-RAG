import axios from 'axios';
import { getTTSUrl } from '@/utils/helpers';

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

  const response = await axios.post(
    getTTSUrl(),
    request,
    {
      headers: { 'Content-Type': 'application/json' },
      responseType: 'blob',
    }
  );
  return response.data;
};
