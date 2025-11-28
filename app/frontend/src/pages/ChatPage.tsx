import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { TTSSettings } from '@/components/chat/TTSSettings';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/store/chatStore';
import { Trash2, Settings2 } from 'lucide-react';
import { useState, useRef, useEffect, useCallback } from 'react';

export function ChatPage() {
  const clearMessages = useChatStore((state) => state.clearMessages);
  const [showTTSSettings, setShowTTSSettings] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close settings panel
  const closeSettings = useCallback(() => {
    setShowTTSSettings(false);
  }, []);

  // Handle click outside
  useEffect(() => {
    if (!showTTSSettings) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      // Don't close if clicking the toggle button or inside the settings panel
      if (
        settingsRef.current?.contains(target) ||
        buttonRef.current?.contains(target)
      ) {
        return;
      }
      closeSettings();
    };

    // Handle ESC key
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeSettings();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showTTSSettings, closeSettings]);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-4 md:px-6 py-3 md:py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto gap-2">
          <div className="min-w-0 flex-1 pl-12 md:pl-0">
            <h1 className="text-xl md:text-2xl font-bold">Chat</h1>
            <p className="text-xs md:text-sm text-muted-foreground hidden sm:block">
              Ask questions and get AI-powered answers
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              ref={buttonRef}
              variant="outline"
              size="sm"
              onClick={() => setShowTTSSettings(!showTTSSettings)}
              className="shrink-0"
              aria-label="Toggle voice settings"
              aria-expanded={showTTSSettings}
            >
              <Settings2 className="h-4 w-4 md:mr-2" aria-hidden="true" />
              <span className="hidden md:inline">Voice</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearMessages}
              className="shrink-0"
            >
              <Trash2 className="h-4 w-4 md:mr-2" aria-hidden="true" />
              <span className="hidden md:inline">Clear Chat</span>
            </Button>
          </div>
        </div>
      </div>

      {/* TTS Settings Panel */}
      {showTTSSettings && (
        <div 
          ref={settingsRef}
          className="border-b border-border bg-card/30 px-4 md:px-6 py-3 animate-in slide-in-from-top-2 duration-200"
        >
          <div className="max-w-4xl mx-auto">
            <TTSSettings />
          </div>
        </div>
      )}

      <div className="flex-1 flex flex-col overflow-hidden">
        <MessageList />
        <ChatInput />
      </div>
    </div>
  );
}
