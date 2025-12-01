import { useState } from 'react';
import { useUploadDocuments } from '@/hooks/useVectorStores';
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { IconLabel } from '@/components/ui/icon-label';
import { FileText, Loader2 } from 'lucide-react';

interface CreateDocumentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  storeId: number;
  storeName: string;
}

/**
 * Dialog for creating text documents directly in the UI.
 * Converts text to File object and uses existing upload API.
 * 
 * CRITICAL: Reuses uploadDocuments mutation - NO duplicate API logic.
 */
export function CreateDocumentDialog({
  open,
  onOpenChange,
  storeId,
  storeName,
}: Readonly<CreateDocumentDialogProps>) {
  const [filename, setFilename] = useState('');
  const [content, setContent] = useState('');
  
  const uploadDocuments = useUploadDocuments();

  const handleCreate = async () => {
    if (!filename.trim() || !content.trim()) return;

    // Validate filename has extension
    const hasExtension = /\.(txt|md)$/i.test(filename.trim());
    if (!hasExtension) {
      handleError(
        new Error('Filename must have .txt or .md extension'),
        'Invalid filename',
        { title: 'Validation Error' }
      );
      return;
    }

    try {
      // Convert text to File object to reuse existing upload API
      const blob = new Blob([content], { type: 'text/plain' });
      const file = new File([blob], filename.trim(), { type: 'text/plain' });

      await uploadDocuments.mutateAsync({
        storeId,
        files: [file],
      });

      showSuccess('Document Created', `Successfully created "${filename.trim()}"`);
      
      // Reset form and close
      setFilename('');
      setContent('');
      onOpenChange(false);
    } catch (error) {
      handleError(error, ...ERROR_TEMPLATES.DOCUMENT_UPLOAD(storeId, 1));
    }
  };

  const handleClose = () => {
    if (!uploadDocuments.isPending) {
      setFilename('');
      setContent('');
      onOpenChange(false);
    }
  };

  const isValid = filename.trim() && content.trim() && /\.(txt|md)$/i.test(filename.trim());

  return (
    <Dialog open={open} onOpenChange={(newOpen) => !newOpen && handleClose()}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            <IconLabel icon={<FileText className="h-5 w-5" />} gap="sm">
              Create Text Document
            </IconLabel>
          </DialogTitle>
          <DialogDescription>
            Create a new text document in <strong>{storeName}</strong>. 
            Content will be processed and indexed automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Filename input */}
          <div className="grid gap-2">
            <Label htmlFor="filename">
              Filename <span className="text-destructive">*</span>
            </Label>
            <Input
              id="filename"
              placeholder="my-document.txt or notes.md"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              disabled={uploadDocuments.isPending}
              className={!filename.trim() || /\.(txt|md)$/i.test(filename.trim()) ? '' : 'border-destructive'}
            />
            <p className="text-xs text-muted-foreground">
              Must end with .txt or .md extension
            </p>
          </div>

          {/* Content textarea */}
          <div className="grid gap-2">
            <Label htmlFor="content">
              Content <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="content"
              placeholder="Enter your document content here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={uploadDocuments.isPending}
              rows={12}
              className="resize-none font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              {content.length} characters ({(content.length / 1024).toFixed(1)} KB)
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={uploadDocuments.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleCreate}
            disabled={!isValid || uploadDocuments.isPending}
          >
            {uploadDocuments.isPending ? (
              <IconLabel icon={<Loader2 className="h-4 w-4 animate-spin" />} gap="sm">
                Creating...
              </IconLabel>
            ) : (
              <IconLabel icon={<FileText className="h-4 w-4" />} gap="sm">
                Create Document
              </IconLabel>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
