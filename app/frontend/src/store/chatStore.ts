import { create } from 'zustand';
import { Message } from '@/types/chat';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  selectedStoreId: number | null;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setSelectedStoreId: (storeId: number | null) => void;
}

/**
 * FIXED: Removed activeAudio DOM element from global state
 * Audio playback should be managed locally with refs, not in Zustand
 */
export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
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

  setSelectedStoreId: (storeId) => set({ selectedStoreId: storeId }),
}));
