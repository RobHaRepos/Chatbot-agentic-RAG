import { create } from 'zustand';
import { Message } from '@/types/chat';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  activeAudio: HTMLAudioElement | null;
  selectedStoreId: number | null;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setActiveAudio: (audio: HTMLAudioElement | null) => void;
  stopActiveAudio: () => void;
  setSelectedStoreId: (storeId: number | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  activeAudio: null,
  selectedStoreId: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    })),

  clearMessages: () => set({ messages: [] }),

  setLoading: (loading) => set({ isLoading: loading }),

  setActiveAudio: (audio) => set({ activeAudio: audio }),

  stopActiveAudio: () => {
    const { activeAudio } = get();
    if (activeAudio) {
      try {
        activeAudio.pause();
      } catch (err) {
        console.error('Failed to pause active audio', err);
      } finally {
        set({ activeAudio: null });
      }
    }
  },

  setSelectedStoreId: (storeId) => set({ selectedStoreId: storeId }),
}));
