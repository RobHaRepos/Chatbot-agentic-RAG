import { useEffect } from 'react';
import { useDeleteDocument } from '@/hooks/useVectorStores';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { IconLabel } from '@/components/ui/icon-label';
import { AlertCircle, Trash2, Loader2 } from 'lucide-react';
import type { Document } from '@/types/vectorStore';

interface DeleteDocumentDialogProps {
  readonly storeId: number;
  readonly document: Document;
  readonly open: boolean;
  readonly onClose: () => void;
}

export function DeleteDocumentDialog({ storeId, document, open, onClose }: Readonly<DeleteDocumentDialogProps>) {
  const deleteMutation = useDeleteDocument();

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      deleteMutation.reset();
    }
  }, [open, deleteMutation]);

  const handleDelete = () => {
    deleteMutation.mutate(
      { storeId, docId: document.id },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            <IconLabel icon={<Trash2 className="h-4 w-4" />}>
              Delete Document
            </IconLabel>
          </DialogTitle>
          <DialogDescription>
            This action cannot be undone. All associated chunks will be removed from the FAISS index.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {deleteMutation.isError && (
            <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
              <p className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                Failed to delete document. Please try again.
              </p>
            </div>
          )}

          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
            <p className="text-sm">
              Are you sure you want to delete <span className="font-semibold">{document.filename}</span>?
            </p>
            <div className="mt-2 space-y-1 text-xs text-muted-foreground">
              <p>• File type: {document.file_type}</p>
              <p>• Chunks: {document.chunk_count}</p>
              <p>• Size: {((document.file_size ?? 0) / 1024).toFixed(2)} KB</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={deleteMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Document
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
