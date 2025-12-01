import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { useChatStore } from '@/store/chatStore';
import { sendMessage } from '@/services/api';
import { logger } from '@/services/logger';
import { generateId } from '@/lib/utils';
import { handleError, showError } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';
import { extractResponseText } from '@/types/chat';
import { StoreSelector } from './StoreSelector';

/**
 * FIXED: Uses toast for validation instead of polluting chat history
 * Clean response parsing using extractResponseText utility
 */
export function ChatInput() {
  const [input, setInput] = useState('');
  const { addMessage, updateMessage, setLoading, selectedStoreId } = useChatStore();

  const handleSubmit = async () => {
    const question = input.trim();
    if (!question) return;

    // FIXED: Use toast instead of adding bot message to chat history
    if (!selectedStoreId) {
      showError('Please select a vector store before sending a message', {
        title: 'No Store Selected',
      });
      return;
    }

    const userMessageId = generateId();
    const botMessageId = generateId();

    // Add user message
    addMessage({
      id: userMessageId,
      text: question,
      sender: 'user',
      timestamp: new Date(),
    });

    // Add loading bot message
    addMessage({
      id: botMessageId,
      text: 'Thinking...',
      sender: 'bot',
      timestamp: new Date(),
      isLoading: true,
    });

    setInput('');
    setLoading(true);

    try {
      logger.log('info', 'send_question', { question, store_id: selectedStoreId });

      const response = await sendMessage({
        question,
        store_id: selectedStoreId,
      });

      logger.log('info', 'received_response', { question, result: response.result });

      const answerText = extractResponseText(response);

      // Update bot message
      updateMessage(botMessageId, {
        text: answerText,
        isLoading: false,
      });
    } catch (err: unknown) {
      logger.log('error', 'request_failed', { question, error: String(err) });
      
      handleError(err, ...ERROR_TEMPLATES.CHAT_SEND(selectedStoreId, question));
      
      updateMessage(botMessageId, {
        text: `Error: ${err instanceof Error ? err.message : 'Request failed'}`,
        isLoading: false,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border bg-card/50 p-3 md:p-4">
      <div className="max-w-4xl mx-auto space-y-2 md:space-y-3">
        {/* Store Selector */}
        <IconLabel icon={<span className="text-sm text-muted-foreground">Knowledge base:</span>} gap="sm">
          <StoreSelector />
        </IconLabel>

        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={selectedStoreId ? "Type your question here..." : "Select a knowledge base first..."}
          className="min-h-[80px] md:min-h-[100px] resize-none"
          aria-label="Message input"
          disabled={!selectedStoreId}
        />

        <div className="flex justify-end">
          <Button 
            onClick={handleSubmit} 
            className="w-full sm:w-auto" 
            size="lg" 
            aria-label="Send message"
            disabled={!selectedStoreId}
          >
            <Send className="h-4 w-4 mr-2" aria-hidden="true" />
            Send
          </Button>
        </div>

        <p className="text-xs text-muted-foreground hidden sm:block">
          <strong>Tip:</strong> Press Enter to send, Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}
