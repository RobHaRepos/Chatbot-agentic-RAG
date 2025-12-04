import { useState, useEffect } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { MessageEditor } from './MessageEditor';
import { useUpdateTemplate } from '@/hooks/useTemplates';
import type { Template, MessageBlock } from '@/types/template';
import { TEMPLATE_TYPE_LABELS } from '@/types/template';

interface TemplateEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template: Template;
  onSaved?: () => void;
}

export function TemplateEditDialog({
  open,
  onOpenChange,
  template,
  onSaved,
}: Readonly<TemplateEditDialogProps>) {
  const [name, setName] = useState(template.name);
  const [messages, setMessages] = useState<MessageBlock[]>(template.messages);
  const [isActive, setIsActive] = useState(template.is_active);
  
  const updateMutation = useUpdateTemplate(template.id);

  // Reset form when template changes
  useEffect(() => {
    setName(template.name);
    setMessages(template.messages);
    setIsActive(template.is_active);
  }, [template]);

  const handleSave = async () => {
    try {
      await updateMutation.mutateAsync({
        name,
        messages,
        is_active: isActive,
      });
      onSaved?.();
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to update template:', error);
    }
  };

  const handleMessageChange = (index: number, field: keyof MessageBlock, value: string) => {
    const updated = [...messages];
    updated[index] = { ...updated[index], [field]: value };
    setMessages(updated);
  };

  const handleAddMessage = () => {
    setMessages([...messages, { role: 'user', content: '' }]);
  };

  const handleRemoveMessage = (index: number) => {
    if (messages.length > 1) {
      setMessages(messages.filter((_, i) => i !== index));
    }
  };

  const hasChanges =
    name !== template.name ||
    isActive !== template.is_active ||
    JSON.stringify(messages) !== JSON.stringify(template.messages);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Template</DialogTitle>
          <DialogDescription>
            {TEMPLATE_TYPE_LABELS[template.template_type]} - Customize the prompt messages
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
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

          {/* Active Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Active</Label>
              <p className="text-sm text-muted-foreground">
                Only active templates are used during chat
              </p>
            </div>
            <Switch checked={isActive} onCheckedChange={setIsActive} />
          </div>

          {/* Messages Editor */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Messages</Label>
              <Button variant="outline" size="sm" onClick={handleAddMessage}>
                Add Message
              </Button>
            </div>
            <div className="space-y-4">
              {messages.map((message, index) => (
                <MessageEditor
                  key={`${message.role}-${index}`}
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
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={!hasChanges || updateMutation.isPending}
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
