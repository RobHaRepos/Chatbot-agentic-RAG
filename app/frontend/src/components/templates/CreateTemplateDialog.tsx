import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { MessageEditor } from './MessageEditor';
import { useCreateTemplate } from '@/hooks/useTemplates';
import type { MessageBlock, TemplateType } from '@/types/template';
import { TEMPLATE_TYPE_LABELS, TEMPLATE_TYPE_DESCRIPTIONS } from '@/types/template';

interface CreateTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  storeId: number;
  onCreated?: () => void;
}

interface MessageWithId extends MessageBlock {
  id: string;
}

const createMessageWithId = (msg: MessageBlock): MessageWithId => ({
  ...msg,
  id: crypto.randomUUID(),
});

const DEFAULT_MESSAGES: Record<TemplateType, MessageBlock[]> = {
  retrieve_or_respond: [
    {
      role: 'system',
      content: `You are an AI assistant that helps users find information.
Based on the user's question, decide whether you need to retrieve documents or can respond directly.
If the question requires specific information from the knowledge base, retrieve documents first.
Return JSON: {{"action":"retrieve", "query":"<query>"}} or {{"action":"clarify", "answer":"<response>"}}`,
    },
    {
      role: 'user',
      content: 'User question: {user_input}',
    },
  ],
  generate_answer: [
    {
      role: 'system',
      content: `You are a helpful assistant. Use the following retrieved context to answer the user's question.
If you cannot find the answer in the context, say so honestly.
USER QUESTION: {user_input}
INFORMATION: {retrieved_information}
CONTEXT: {context}`,
    },
  ],
};

export function CreateTemplateDialog({
  open,
  onOpenChange,
  storeId,
  onCreated,
}: Readonly<CreateTemplateDialogProps>) {
  const [name, setName] = useState('');
  const [templateType, setTemplateType] = useState<TemplateType | ''>('');
  const [messages, setMessages] = useState<MessageWithId[]>([createMessageWithId({ role: 'system', content: '' })]);

  const createMutation = useCreateTemplate();

  const handleTemplateTypeChange = (value: TemplateType) => {
    setTemplateType(value);
    // Pre-populate with default messages for this type
    setMessages(DEFAULT_MESSAGES[value].map(createMessageWithId));
    // Auto-generate a name if empty
    if (!name) {
      setName(TEMPLATE_TYPE_LABELS[value]);
    }
  };

  const handleSave = async () => {
    if (!templateType) return;

    try {
      await createMutation.mutateAsync({
        name,
        template_type: templateType,
        store_id: storeId,
        messages: messages.map(({ role, content }) => ({ role, content })),
      });
      // Reset form
      setName('');
      setTemplateType('');
      setMessages([createMessageWithId({ role: 'system', content: '' })]);
      onCreated?.();
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to create template:', error);
    }
  };

  const handleMessageChange = (index: number, field: keyof MessageBlock, value: string) => {
    const updated = [...messages];
    updated[index] = { ...updated[index], [field]: value };
    setMessages(updated);
  };

  const handleAddMessage = () => {
    setMessages([...messages, createMessageWithId({ role: 'user', content: '' })]);
  };

  const handleRemoveMessage = (index: number) => {
    if (messages.length > 1) {
      setMessages(messages.filter((_, i) => i !== index));
    }
  };

  const handleClose = (openState: boolean) => {
    if (!openState) {
      // Reset form when closing
      setName('');
      setTemplateType('');
      setMessages([createMessageWithId({ role: 'system', content: '' })]);
    }
    onOpenChange(openState);
  };

  const isValid = name.trim() && templateType && messages.length > 0 && messages.every(m => m.content.trim());

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Template</DialogTitle>
          <DialogDescription>
            Create a new prompt template for this vector store
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Template Type */}
          <div className="space-y-2">
            <Label htmlFor="template-type">Template Type</Label>
            <Select value={templateType} onValueChange={handleTemplateTypeChange}>
              <SelectTrigger id="template-type">
                <SelectValue placeholder="Select a template type" />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(TEMPLATE_TYPE_LABELS) as TemplateType[]).map((type) => (
                  <SelectItem key={type} value={type}>
                    {TEMPLATE_TYPE_LABELS[type]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {templateType && (
              <p className="text-sm text-muted-foreground">
                {TEMPLATE_TYPE_DESCRIPTIONS[templateType]}
              </p>
            )}
          </div>

          {/* Template Name */}
          <div className="space-y-2">
            <Label htmlFor="template-name">Template Name</Label>
            <Input
              id="template-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter template name"
            />
          </div>

          {/* Messages Editor */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Messages</Label>
              <Button variant="outline" size="sm" onClick={handleAddMessage}>
                Add Message
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Use {'{'}<code>context</code>{'}'} for retrieved documents and {'{'}<code>question</code>{'}'} for user input
            </p>
            <div className="space-y-4">
              {messages.map((message, index) => (
                <MessageEditor
                  key={message.id}
                  message={message}
                  index={index}
                  canRemove={messages.length > 1}
                  onChange={(field, value) => handleMessageChange(index, field, value)}
                  onRemove={() => handleRemoveMessage(index)}
                />
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => handleClose(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!isValid || createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating...' : 'Create Template'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
