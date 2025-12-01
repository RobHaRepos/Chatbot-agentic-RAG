import { useEffect, useRef } from 'react';
import { Database, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { IconLabel } from '@/components/ui/icon-label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/radix-select';
import { useStores } from '@/hooks/useVectorStores';
import { useChatStore } from '@/store/chatStore';
import { SkeletonSelect } from '@/components/common/SkeletonSelect';

/**
 * FIXED: Prevents infinite loop by tracking if auto-selection already happened
 * Better accessibility, proper keyboard navigation, consistent styling
 */
export function StoreSelector() {
  const { selectedStoreId, setSelectedStoreId } = useChatStore();
  const hasAutoSelectedRef = useRef(false);
  
  // Use React Query hook for consistency
  const { data: stores = [], isLoading, error, refetch } = useStores();

  // Auto-select first active store if none selected (only once)
  useEffect(() => {
    if (!selectedStoreId && stores.length > 0 && !hasAutoSelectedRef.current) {
      const activeStore = stores.find(s => s.is_active) || stores[0];
      setSelectedStoreId(activeStore.id);
      hasAutoSelectedRef.current = true;
    }
  }, [stores, selectedStoreId, setSelectedStoreId]);

  if (isLoading) {
    return <SkeletonSelect />;
  }

  if (error) {
    return (
      <IconLabel icon={<AlertCircle className="h-4 w-4" />} gap="sm" className="text-sm text-destructive">
        <span>Failed to load stores</span>
        <Button variant="ghost" size="sm" onClick={() => refetch()}>
          Retry
        </Button>
      </IconLabel>
    );
  }

  if (stores.length === 0) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Database className="h-4 w-4" />
        <span>No vector stores available</span>
      </div>
    );
  }

  return (
    <Select
      value={selectedStoreId?.toString() || ''}
      onValueChange={(value) => setSelectedStoreId(Number.parseInt(value, 10))}
    >
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a store" />
      </SelectTrigger>
      <SelectContent>
        {stores.map((store) => (
          <SelectItem key={store.id} value={store.id.toString()}>
            <div className="flex items-center justify-between w-full">
              <span className="font-medium">{store.name}</span>
              {!store.is_active && (
                <span className="text-xs text-muted-foreground ml-2">(inactive)</span>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
