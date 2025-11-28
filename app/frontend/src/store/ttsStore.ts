import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { DEFAULT_VOICE_ID, DEFAULT_SPEED } from '@/types/tts';

interface TTSState {
  voice: string;
  speed: number;
  setVoice: (voice: string) => void;
  setSpeed: (speed: number) => void;
  resetToDefaults: () => void;
}

export const useTTSStore = create<TTSState>()(
  persist(
    (set) => ({
      voice: DEFAULT_VOICE_ID,
      speed: DEFAULT_SPEED,

      setVoice: (voice) => set({ voice }),
      setSpeed: (speed) => set({ speed }),
      resetToDefaults: () => set({ voice: DEFAULT_VOICE_ID, speed: DEFAULT_SPEED }),
    }),
    {
      name: 'tts-settings', // localStorage key
    }
  )
);
