import { useState } from 'react';
import { useCreateStore, useEmbeddingModels } from '@/hooks/useVectorStores';
import { useFormField, validationRules } from '@/hooks/useFormValidation';
import { handleError, showSuccess } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';
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
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/radix-select';
import { IconLabel } from '@/components/ui/icon-label';
import { Loader2, Plus } from 'lucide-react';
import type { EmbeddingModel } from '@/types/vectorStore';
import { cn } from '@/lib/utils';

interface CreateStoreModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * CRITICAL FIX: Now uses useFormField hook instead of 3 separate useState calls
 * Eliminates form state management duplication across modals
 */
export function CreateStoreModal({ open, onOpenChange }: Readonly<CreateStoreModalProps>) {
  const nameField = useFormField('', [
    validationRules.required('Store name is required'),
    validationRules.minLength(3, 'Name must be at least 3 characters'),
  ]);
  const descriptionField = useFormField('');
  const [embeddingModelId, setEmbeddingModelId] = useState<string>('');

  const { data: embeddingModels, isLoading: modelsLoading } = useEmbeddingModels();
  const createStore = useCreateStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all fields
    if (!nameField.validate() || !embeddingModelId) return;

    try {
      await createStore.mutateAsync({
        name: nameField.value.trim(),
        description: descriptionField.value.trim() || undefined,
        embedding_model_id: Number.parseInt(embeddingModelId, 10),
      });
      
      showSuccess('Store Created', `Successfully created store "${nameField.value.trim()}"`);
      
      // Reset form and close
      nameField.reset();
      descriptionField.reset();
      setEmbeddingModelId('');
      onOpenChange(false);
    } catch (error) {
      handleError(error, ...ERROR_TEMPLATES.STORE_CREATE(nameField.value.trim()));
    }
  };

  const availableModels = embeddingModels?.filter((m: EmbeddingModel) => m.is_available) || [];

  return (
    <Dialog 
      open={open} 
      onOpenChange={(newOpen) => {
        // Prevent closing during submission to avoid data loss
        if (!createStore.isPending) {
          onOpenChange(newOpen);
        }
      }}
    >
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              <IconLabel icon={<Plus className="h-5 w-5" />} gap="sm">
                Create Vector Store
              </IconLabel>
            </DialogTitle>
            <DialogDescription>
              Create a new vector store to organize your documents for RAG.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="My Knowledge Base"
                value={nameField.value}
                onChange={(e) => nameField.setValue(e.target.value)}
                disabled={createStore.isPending}
                className={cn(nameField.error && nameField.isDirty && 'border-destructive')}
              />
              {nameField.error && nameField.isDirty && (
                <p className="text-xs text-destructive">{nameField.error}</p>
              )}
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Optional description of this vector store..."
                value={descriptionField.value}
                onChange={(e) => descriptionField.setValue(e.target.value)}
                disabled={createStore.isPending}
                rows={3}
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="embedding-model">Embedding Model *</Label>
              <Select
                value={embeddingModelId}
                onValueChange={setEmbeddingModelId}
                disabled={createStore.isPending || modelsLoading}
              >
                <SelectTrigger id="embedding-model">
                  <SelectValue placeholder="Select an embedding model" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model: EmbeddingModel) => (
                    <SelectItem key={model.id} value={model.id.toString()}>
                      <div className="flex flex-col">
                        <span>{model.display_name || model.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {model.dimension}d
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {availableModels.length === 0 && !modelsLoading && (
                <p className="text-sm text-destructive">
                  No embedding models available
                </p>
              )}
            </div>
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createStore.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!nameField.isValid || !embeddingModelId || createStore.isPending}
            >
              {createStore.isPending ? (
                <IconLabel icon={<Loader2 className="h-4 w-4 animate-spin" />} gap="sm">
                  Creating...
                </IconLabel>
              ) : (
                'Create Store'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
