import { useUpdateStore } from '@/hooks/useVectorStores';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { cn } from '@/lib/utils';
import { handleError, showSuccess } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';

interface StoreStatusToggleProps {
  storeId: number;
  storeName: string;
  isActive: boolean;
  showLabel?: boolean;
  className?: string;
}

/**
 * CRITICAL NOTE: Backend API requires 'name' field even for partial updates.
 * This is a backend design flaw - VectorStoreUpdate should have all optional fields.
 * FIXED: Proper error handling with toast notifications
 */
export function StoreStatusToggle({
  storeId,
  storeName,
  isActive,
  showLabel = true,
  className,
}: Readonly<StoreStatusToggleProps>) {
  const updateStore = useUpdateStore();

  const handleToggle = async (checked: boolean) => {
    try {
      await updateStore.mutateAsync({
        id: storeId,
        data: { name: storeName, is_active: checked },
      });
      showSuccess(
        'Status Updated',
        `Store "${storeName}" is now ${checked ? 'active' : 'inactive'}`
      );
    } catch (error) {
      handleError(error, ...ERROR_TEMPLATES.STORE_UPDATE(storeId, storeName));
    }
  };

  return (
    <IconLabel 
      icon={
        updateStore.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : (
          <Switch
            id={`store-status-${storeId}`}
            checked={isActive}
            onCheckedChange={handleToggle}
            disabled={updateStore.isPending}
          />
        )
      }
      gap="sm"
      className={className}
    >
      {showLabel && (
        <Label
          htmlFor={`store-status-${storeId}`}
          className={cn(
            "text-sm cursor-pointer",
            isActive ? "text-green-600" : "text-muted-foreground"
          )}
        >
          {isActive ? 'Active' : 'Inactive'}
        </Label>
      )}
    </IconLabel>
  );
}
