import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Trash2 } from 'lucide-react';
import type { MessageBlock } from '@/types/template';

const ROLE_OPTIONS = [
  { value: 'system', label: 'System', color: 'bg-blue-500/10 text-blue-500' },
  { value: 'user', label: 'User', color: 'bg-green-500/10 text-green-500' },
  { value: 'assistant', label: 'Assistant', color: 'bg-purple-500/10 text-purple-500' },
] as const;

interface MessageEditorProps {
  message: MessageBlock;
  index: number;
  canRemove: boolean;
  onChange: (field: keyof MessageBlock, value: string) => void;
  onRemove: () => void;
}

export function MessageEditor({
  message,
  index,
  canRemove,
  onChange,
  onRemove,
}: Readonly<MessageEditorProps>) {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            #{index + 1}
          </Badge>
          <Select
            value={message.role}
            onValueChange={(value: string) => onChange('role', value)}
          >
            <SelectTrigger className="w-32 h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ROLE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <span className={`px-2 py-0.5 rounded text-xs ${option.color}`}>
                    {option.label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {canRemove && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-destructive hover:text-destructive"
            onClick={onRemove}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
      <Textarea
        value={message.content}
        onChange={(e) => onChange('content', e.target.value)}
        placeholder={`Enter ${message.role} message content...`}
        className="min-h-[120px] font-mono text-sm"
      />
      <VariablePlaceholders role={message.role} />
    </div>
  );
}

interface VariablePlaceholdersProps {
  role: string;
}

function VariablePlaceholders({ role }: Readonly<VariablePlaceholdersProps>) {
  // Show available variables based on message role/context
  const variables = [
    { name: '{user_input}', desc: 'The user question' },
    { name: '{retrieved_information}', desc: 'Documents from RAG' },
    { name: '{context}', desc: 'Accumulated context' },
  ];

  if (role !== 'system' && role !== 'user') return null;

  return (
    <div className="flex flex-wrap gap-2 pt-2 border-t">
      <span className="text-xs text-muted-foreground">Variables:</span>
      {variables.map((v) => (
        <code
          key={v.name}
          className="text-xs bg-muted px-1.5 py-0.5 rounded cursor-help"
          title={v.desc}
        >
          {v.name}
        </code>
      ))}
    </div>
  );
}
