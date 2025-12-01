import { Skeleton } from '@/components/ui/skeleton';

/**
 * Skeleton placeholder for select dropdowns during loading
 */
export function SkeletonSelect() {
  return (
    <div className="flex items-center gap-2">
      <Skeleton className="h-4 w-4" />
      <Skeleton className="h-4 w-32" />
    </div>
  );
}
