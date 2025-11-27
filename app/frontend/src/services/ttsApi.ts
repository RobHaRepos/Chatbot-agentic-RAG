import axios from 'axios';
import { getTTSUrl } from '@/utils/helpers';

export const generateSpeech = async (text: string): Promise<Blob> => {
  const response = await axios.post(
    getTTSUrl(),
    { text },
    {
      headers: { 'Content-Type': 'application/json' },
      responseType: 'blob',
    }
  );
  return response.data;
};
