import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, ArrowLeft, FileText, Cpu, Hash, Upload, Trash2 } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { ErrorState } from '@/components/common';
import { SkeletonCard } from '@/components/common/SkeletonCard';
import { PageHeader } from '@/components/layout/PageHeader';
import { PageContent } from '@/components/layout/PageContent';
import { RetrievalTestPanel } from '@/components/retrieval';
import { StoreStatusToggle } from '@/components/vector-stores/StoreStatusToggle';
import { UploadDocumentsModal } from '@/components/vector-stores/UploadDocumentsModal';
import { CreateDocumentDialog } from '@/components/vector-stores/CreateDocumentDialog';
import { DeleteStoreDialog } from '@/components/vector-stores/DeleteStoreDialog';
import { DocumentList } from '@/components/vector-stores/DocumentList';
import { useStore } from '@/hooks/useVectorStores';
import { useModal } from '@/hooks/useModal';

// Loading state configuration
const SKELETON_CARD_COUNT = 3; // Matches info card count: Documents, Chunks, Embedding Model

export function StoreDetailsPage() {
  const { storeId } = useParams<{ storeId: string }>();
  const navigate = useNavigate();
  const id = storeId ? Number.parseInt(storeId) : 0;
  
  // React Query hook
  const { data: store, isLoading, error, refetch } = useStore(id);
  
  // Modal states - FIXED: Using useModal hook instead of duplicate useState
  const uploadModal = useModal();
  const createDocumentDialog = useModal();
  const deleteDialog = useModal();

  const handleUploadModalChange = (open: boolean) => {
    uploadModal.setOpen(open);
    // Reload store when modal closes to update document count
    if (!open) {
      refetch();
    }
  };

  const handleCreateDocumentDialogChange = (open: boolean) => {
    createDocumentDialog.setOpen(open);
    // Reload store when dialog closes to update document count
    if (!open) {
      refetch();
    }
  };

  const handleDeleted = () => {
    navigate('/vectorstores');
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader 
          title="Store Details"
          icon={<Database className="h-6 w-6 text-primary" />}
        />
        <PageContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Array.from({ length: SKELETON_CARD_COUNT }, () => crypto.randomUUID()).map((id) => (
              <SkeletonCard key={id} />
            ))}
          </div>
        </PageContent>
      </div>
    );
  }

  if (error || !store) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Store Details"
          backButton={
            <Button variant="ghost" size="sm" onClick={() => navigate('/vectorstores')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Stores
            </Button>
          }
        />
        <div className="flex items-center justify-center flex-1 p-6">
          <ErrorState
            message={error instanceof Error ? error.message : 'Store not found'}
            onRetry={() => refetch()}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={store.name}
        description={store.description || undefined}
        icon={<Database className="h-6 w-6 text-primary" />}
        backButton={
          <Button variant="ghost" size="sm" onClick={() => navigate('/vectorstores')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Stores
          </Button>
        }
        actions={
          <>
            <StoreStatusToggle
              storeId={store.id}
              storeName={store.name}
              isActive={store.is_active}
            />
            <Button variant="outline" size="sm" onClick={createDocumentDialog.open}>
              <FileText className="h-4 w-4 mr-2" />
              Create Document
            </Button>
            <Button variant="outline" size="sm" onClick={uploadModal.open}>
              <Upload className="h-4 w-4 mr-2" />
              Upload Files
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={deleteDialog.open}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Store
            </Button>
          </>
        }
      />

      <PageContent>
        {/* Store Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  <IconLabel icon={<FileText className="h-4 w-4" />} gap="sm">
                    Documents
                  </IconLabel>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{store.document_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  <IconLabel icon={<Hash className="h-4 w-4" />} gap="sm">
                    Chunks
                  </IconLabel>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{store.chunk_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  <IconLabel icon={<Cpu className="h-4 w-4" />} gap="sm">
                    Embedding Model
                  </IconLabel>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm font-medium">
                  {store.embedding_model.display_name || store.embedding_model.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {store.embedding_model.dimension} dimensions
                </p>
              </CardContent>
            </Card>
          </div>

        {/* Retrieval Test - Using Reusable Component */}
        <RetrievalTestPanel storeId={store.id} />

        {/* Document Management */}
        <Card>
          <CardHeader>
            <CardDescription>
              <IconLabel icon={<FileText className="h-4 w-4" />} gap="sm">
                Documents
              </IconLabel>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DocumentList storeId={store.id} />
          </CardContent>
        </Card>
      </PageContent>

      {/* Modals */}
      <CreateDocumentDialog
        open={createDocumentDialog.isOpen}
        onOpenChange={handleCreateDocumentDialogChange}
        storeId={store.id}
        storeName={store.name}
      />
      <UploadDocumentsModal
        open={uploadModal.isOpen}
        onOpenChange={handleUploadModalChange}
        storeId={store.id}
        storeName={store.name}
      />
      <DeleteStoreDialog
        open={deleteDialog.isOpen}
        onOpenChange={deleteDialog.setOpen}
        storeId={store.id}
        storeName={store.name}
        onDeleted={handleDeleted}
      />
    </div>
  );
}
