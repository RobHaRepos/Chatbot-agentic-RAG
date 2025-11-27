import { Message } from '@/types/chat';
import { cn } from '@/lib/utils';
import { formatDate } from '@/utils/helpers';
import { TTSButton } from './TTSButton';
import { Loader2 } from 'lucide-react';

interface MessageItemProps {
  readonly message: Message;
}

export function MessageItem({ message }: Readonly<MessageItemProps>) {
  const isUser = message.sender === 'user';

  return (
    <div
      className={cn(
        'flex gap-2 md:gap-3 max-w-[95%] sm:max-w-[85%] md:max-w-[80%] animate-in fade-in slide-in-from-bottom-2',
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
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
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            message.text
          )}
        </div>
      </div>
    </div>
  );
}
