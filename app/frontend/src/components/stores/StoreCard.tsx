import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Database, ExternalLink } from 'lucide-react';
import type { VectorStore } from '@/types/vectorStore';

interface StoreCardProps {
  store: VectorStore;
  isSelected?: boolean;
  onSelect?: () => void;
  onViewDetails?: () => void;
  showViewButton?: boolean;
}

/**
 * A card component for displaying vector store information.
 * Can be interactive (selectable) or static.
 */
export function StoreCard({
  store,
  isSelected = false,
  onSelect,
  onViewDetails,
  showViewButton = true,
}: Readonly<StoreCardProps>) {
  const isClickable = !!onSelect;

  return (
    <Card
      className={`
        transition-all
        ${isClickable ? 'cursor-pointer hover:border-primary/50' : ''}
        ${isSelected ? 'border-primary ring-1 ring-primary' : ''}
      `}
      onClick={onSelect}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">{store.name}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={store.is_active ? 'default' : 'secondary'}>
              {store.is_active ? 'Active' : 'Inactive'}
            </Badge>
            {showViewButton && onViewDetails && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails();
                }}
                title="View details"
              >
                <ExternalLink className="h-3 w-3" />
              </Button>
            )}
          </div>
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
}
