import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { TTSSettings } from '@/components/chat/TTSSettings';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/layout/PageHeader';
import { useChatStore } from '@/store/chatStore';
import { useClickOutside } from '@/hooks/useClickOutside';
import { useModal } from '@/hooks/useModal';
import { Trash2, Settings2, MessageSquare } from 'lucide-react';
import { useRef } from 'react';

/**
 * FIXED: Uses useClickOutside hook instead of duplicate click-outside logic
 * FIXED: Uses useModal hook for settings panel state
 */
export function ChatPage() {
  const clearMessages = useChatStore((state) => state.clearMessages);
  const settingsPanel = useModal();
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Use custom hook for click-outside detection (exclude button from detection)
  const settingsRef = useClickOutside<HTMLDivElement>(
    settingsPanel.close,
    settingsPanel.isOpen,
    [buttonRef]
  );

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Chat"
        description="Ask questions and get AI-powered answers"
        icon={<MessageSquare className="h-6 w-6 text-primary" />}
        actions={
          <>
            <Button
              ref={buttonRef}
              variant="outline"
              size="sm"
              onClick={settingsPanel.toggle}
              className="shrink-0"
              aria-label="Toggle voice settings"
              aria-expanded={settingsPanel.isOpen}
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
          </>
        }
      />

      {/* TTS Settings Panel */}
      {settingsPanel.isOpen && (
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
