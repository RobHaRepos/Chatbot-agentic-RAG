import { useState, useEffect } from 'react';
import { useUpdateDocument, useDocument } from '@/hooks/useVectorStores';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { IconLabel } from '@/components/ui/icon-label';
import { AlertCircle, FileText, Loader2 } from 'lucide-react';

interface EditDocumentDialogProps {
  readonly storeId: number;
  readonly docId: number;
  readonly open: boolean;
  readonly onClose: () => void;
}

export function EditDocumentDialog({ storeId, docId, open, onClose }: Readonly<EditDocumentDialogProps>) {
  const { data: document, isLoading, error: fetchError } = useDocument(storeId, docId);
  const updateMutation = useUpdateDocument();

  const [filename, setFilename] = useState('');
  const [content, setContent] = useState('');
  const [errors, setErrors] = useState<{ filename?: string; content?: string }>({});

  // Load initial values when document loads
  useEffect(() => {
    if (document) {
      setFilename(document.filename);
      setContent(document.content);
    }
  }, [document]);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setErrors({});
      updateMutation.reset();
    }
  }, [open, updateMutation]);

  const validateFilename = (value: string): string | undefined => {
    if (!value.trim()) {
      return 'Filename is required';
    }
    if (value.length > 512) {
      return 'Filename must be less than 512 characters';
    }
    const extension = value.split('.').pop()?.toLowerCase();
    if (!extension || !['txt', 'md'].includes(extension)) {
      return 'Filename must end with .txt or .md';
    }
    return undefined;
  };

  const validateContent = (value: string): string | undefined => {
    if (!value.trim()) {
      return 'Content cannot be empty';
    }
    return undefined;
  };

  const handleSubmit = () => {
    const filenameError = validateFilename(filename);
    const contentError = validateContent(content);

    if (filenameError || contentError) {
      setErrors({ filename: filenameError, content: contentError });
      return;
    }

    setErrors({});

    // Only send changed fields
    const updates: { filename?: string; content?: string } = {};
    if (filename !== document?.filename) updates.filename = filename;
    if (content !== document?.content) updates.content = content;

    if (Object.keys(updates).length === 0) {
      onClose();
      return;
    }

    updateMutation.mutate(
      { storeId, docId, data: updates },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  const handleFilenameChange = (value: string) => {
    setFilename(value);
    if (errors.filename) {
      setErrors({ ...errors, filename: validateFilename(value) });
    }
  };

  const handleContentChange = (value: string) => {
    setContent(value);
    if (errors.content) {
      setErrors({ ...errors, content: validateContent(value) });
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>
            <IconLabel icon={<FileText className="h-4 w-4" />}>
              Edit Document
            </IconLabel>
          </DialogTitle>
          <DialogDescription>
            Modify the document filename or content. Changes to content will re-index all chunks.
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {!isLoading && fetchError && (
          <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
            <p className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              Failed to load document. Please try again.
            </p>
          </div>
        )}

        {!isLoading && !fetchError && (
          <div className="space-y-4">
            {updateMutation.isError && (
              <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
                <p className="flex items-center gap-2 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  Failed to update document. Please try again.
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="filename">Filename</Label>
              <Input
                id="filename"
                value={filename}
                onChange={(e) => handleFilenameChange(e.target.value)}
                placeholder="document.txt"
                disabled={updateMutation.isPending}
              />
              {errors.filename && (
                <p className="text-sm text-destructive">{errors.filename}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">Content</Label>
              <Textarea
                id="content"
                value={content}
                onChange={(e) => handleContentChange(e.target.value)}
                placeholder="Enter document content..."
                rows={15}
                className="font-mono text-sm"
                disabled={updateMutation.isPending}
              />
              {errors.content && (
                <p className="text-sm text-destructive">{errors.content}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {content.length} characters
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={updateMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading || updateMutation.isPending || !!fetchError}
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              'Update Document'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
