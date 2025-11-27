import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/store/chatStore';
import { Trash2 } from 'lucide-react';

export function ChatPage() {
  const clearMessages = useChatStore((state) => state.clearMessages);

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
          <Button
            variant="outline"
            size="sm"
            onClick={clearMessages}
            className="shrink-0"
          >
            <Trash2 className="h-4 w-4 md:mr-2" />
            <span className="hidden md:inline">Clear Chat</span>
          </Button>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <MessageList />
        <ChatInput />
      </div>
    </div>
  );
}
