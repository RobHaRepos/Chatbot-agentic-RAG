import { Link } from 'react-router-dom';
import { Database, Plus } from 'lucide-react';
import { useStores } from '@/hooks/useVectorStores';
import { useModal } from '@/hooks/useModal';
import { StoreCard, CreateStoreModal } from '@/components/vector-stores';
import { PageHeader } from '@/components/layout/PageHeader';
import { PageContent } from '@/components/layout/PageContent';
import { ErrorState, EmptyState } from '@/components/common';
import { SkeletonCard } from '@/components/common/SkeletonCard';
import { RetrievalTestPanel } from '@/components/retrieval';
import { Button } from '@/components/ui/button';

// Loading state configuration
const SKELETON_CARD_COUNT = 6;

export function VectorStoresPage() {
  const createModal = useModal();

  // React Query hooks
  const { data: stores = [], isLoading, error, refetch } = useStores();

  const activeStores = stores.filter((s) => s.is_active);

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader 
          title="Vector Stores" 
          description="Manage your document stores"
          icon={<Database className="h-6 w-6 text-primary" />}
        />
        <PageContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: SKELETON_CARD_COUNT }, () => crypto.randomUUID()).map((id) => (
              <SkeletonCard key={id} />
            ))}
          </div>
        </PageContent>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader title="Vector Stores" description="Manage your document stores" />
        <div className="flex items-center justify-center flex-1 p-6">
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load stores'}
            onRetry={() => refetch()}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Vector Stores"
        description="Manage your document stores"
        icon={<Database className="h-6 w-6 text-primary" />}
        actions={
          <Button onClick={createModal.open}>
            <Plus className="h-4 w-4 mr-2" />
            Create Store
          </Button>
        }
      />

      <PageContent>
        {/* Store Grid */}
        {stores.length === 0 ? (
          <EmptyState
            icon={<Database className="h-12 w-12" />}
            message="No vector stores found. Create your first store to get started."
            action={
              <Button onClick={createModal.open}>
                <Plus className="h-4 w-4 mr-2" />
                Create Store
              </Button>
            }
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {stores.map((store) => (
              <Link key={store.id} to={`/vectorstores/${store.id}`}>
                <StoreCard store={store} />
              </Link>
            ))}
          </div>
        )}

        {/* Query Section - FIXED: Using unified RetrievalTestPanel in multi-store mode */}
        {activeStores.length > 0 && (
          <RetrievalTestPanel stores={activeStores} />
        )}
      </PageContent>

      {/* Create Store Modal */}
      <CreateStoreModal
        open={createModal.isOpen}
        onOpenChange={createModal.setOpen}
      />
    </div>
  );
}
