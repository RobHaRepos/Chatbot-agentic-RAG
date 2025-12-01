import { memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import type { VectorStore } from '@/types/vectorStore';

interface StoreCardProps {
  store: VectorStore;
}

/**
 * FIXED: Memoized to prevent re-renders when other stores change
 * Displays store name, status, description, and stats.
 */
export const StoreCard = memo(function StoreCard({ store }: Readonly<StoreCardProps>) {
  return (
    <Card className="transition-all hover:border-primary/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <IconLabel icon={<Database className="h-4 w-4 text-primary" />} gap="sm">
            <CardTitle className="text-base">{store.name}</CardTitle>
          </IconLabel>
          <Badge variant={store.is_active ? 'default' : 'secondary'}>
            {store.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
        {store.description && (
          <CardDescription className="text-xs">{store.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {store.document_count} docs • {store.chunk_count} chunks
          </span>
          <span>{store.embedding_model.display_name || store.embedding_model.name}</span>
        </div>
      </CardContent>
    </Card>
  );
});
