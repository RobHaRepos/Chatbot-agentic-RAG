import { useDeleteStore } from '@/hooks/useVectorStores';
import { handleError, showSuccess } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { IconLabel } from '@/components/ui/icon-label';
import { Loader2, Trash2 } from 'lucide-react';

interface DeleteStoreDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  storeId: number;
  storeName: string;
  onDeleted?: () => void;
}

export function DeleteStoreDialog({
  open,
  onOpenChange,
  storeId,
  storeName,
  onDeleted,
}: Readonly<DeleteStoreDialogProps>) {
  const deleteStore = useDeleteStore();

  const handleDelete = async () => {
    try {
      await deleteStore.mutateAsync(storeId);
      showSuccess('Store Deleted', `Successfully deleted store "${storeName}"`);
      onOpenChange(false);
      onDeleted?.();
    } catch (error) {
      handleError(error, ...ERROR_TEMPLATES.STORE_DELETE(storeId, storeName));
    }
  };

  return (
    <AlertDialog 
      open={open} 
      onOpenChange={(newOpen) => {
        // Prevent closing during deletion
        if (!deleteStore.isPending) {
          onOpenChange(newOpen);
        }
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            <IconLabel icon={<Trash2 className="h-5 w-5" />} gap="sm" className="text-destructive">
              Delete Vector Store
            </IconLabel>
          </AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete <strong>"{storeName}"</strong>?
            <br /><br />
            This will permanently remove the vector store and all its documents.
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteStore.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleteStore.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteStore.isPending ? (
              <IconLabel icon={<Loader2 className="h-4 w-4 animate-spin" />} gap="sm">
                Deleting...
              </IconLabel>
            ) : (
              'Delete Store'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
