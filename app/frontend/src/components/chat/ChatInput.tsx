import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { sendMessage } from '@/services/chatApi';
import { logger } from '@/services/logger';
import { generateId } from '@/utils/helpers';
import { StoreSelector } from './StoreSelector';

export function ChatInput() {
  const [input, setInput] = useState('');
  const { addMessage, updateMessage, setLoading, selectedStoreId } = useChatStore();

  const handleSubmit = async () => {
    const question = input.trim();
    if (!question) return;

    if (!selectedStoreId) {
      // Show error if no store selected
      const errorId = generateId();
      addMessage({
        id: errorId,
        text: 'Please select a vector store before sending a message.',
        sender: 'bot',
        timestamp: new Date(),
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

      // Parse response
      let answerText = '';
      if (typeof response.result === 'string') {
        answerText = response.result;
      } else if (response.result?.answer) {
        answerText = typeof response.result.answer === 'object'
          ? JSON.stringify(response.result.answer, null, 2)
          : String(response.result.answer);
      } else if (response.result?.text) {
        answerText = String(response.result.text);
      } else {
        answerText = JSON.stringify(response.result, null, 2);
      }

      // Update bot message
      updateMessage(botMessageId, {
        text: answerText,
        isLoading: false,
      });
    } catch (err: any) {
      logger.log('error', 'request_failed', { question, error: String(err) });
      
      updateMessage(botMessageId, {
        text: `Error: ${err.message || 'Request failed'}`,
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
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Knowledge base:</span>
          <StoreSelector />
        </div>

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
