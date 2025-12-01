import { memo } from 'react';
import { Message } from '@/types/chat';
import { cn, formatDate } from '@/lib/utils';
import { TTSButton } from './TTSButton';
import { Loader2 } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';

interface MessageItemProps {
  readonly message: Message;
}

/**
 * FIXED: Memoized to prevent re-renders when other messages change
 */
export const MessageItem = memo(function MessageItem({ message }: Readonly<MessageItemProps>) {
  const isUser = message.sender === 'user';

  return (
    <article
      className={cn(
        'flex gap-2 md:gap-3 max-w-[95%] sm:max-w-[85%] md:max-w-[80%] animate-in fade-in slide-in-from-bottom-2',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
      aria-label={`Message from ${isUser ? 'you' : 'assistant'}`}
      aria-busy={message.isLoading}
    >
      {!isUser && (
        <div className="flex-shrink-0">
          <TTSButton text={message.text} disabled={message.isLoading} />
        </div>
      )}

      <div
        className={cn(
          'rounded-lg px-3 py-2 md:px-4 md:py-3 shadow-sm',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-card border border-border'
        )}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium opacity-70">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="text-xs opacity-50">
            {formatDate(message.timestamp)}
          </span>
        </div>

        <div className="text-sm whitespace-pre-wrap break-words">
          {message.isLoading ? (
            <output aria-label="Loading response">
              <IconLabel icon={<Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />} gap="sm">
                <span>Thinking...</span>
              </IconLabel>
            </output>
          ) : (
            message.text
          )}
        </div>
      </div>
    </article>
  );
});
