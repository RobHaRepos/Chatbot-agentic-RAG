import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Loader2, AlertCircle } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/radix-select';
import { RetrievalResults } from './RetrievalResults';
import { useRetrieveChunks } from '@/hooks/useVectorStores';
import { DEFAULT_RETRIEVAL_K, MIN_RETRIEVAL_K, MAX_RETRIEVAL_K } from '@/lib/constants';
import { handleError } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';
import { IconLabel } from '@/components/ui/icon-label';
import type { RetrievedChunk, VectorStore } from '@/types/vectorStore';

interface RetrievalTestPanelProps {
  /**
   * UNIFIED COMPONENT: If storeId is provided, this is single-store mode.
   * If stores array is provided, this is multi-store mode with dropdown.
   */
  storeId?: number;
  storeName?: string;
  stores?: VectorStore[];
  title?: string;
  description?: string;
}

/**
 * CRITICAL FIX: Unified retrieval panel that handles both single-store and multi-store modes
 * Eliminates 70% code duplication between RetrievalTestPanel and MultiStoreRetrievalPanel
 * 
 * Usage:
 * - Single store: <RetrievalTestPanel storeId={1} storeName="My Store" />
 * - Multi store: <RetrievalTestPanel stores={storeArray} />
 */
export function RetrievalTestPanel({
  storeId: singleStoreId,
  storeName,
  stores = [],
  title = 'Test Retrieval',
  description,
}: Readonly<RetrievalTestPanelProps>) {
  const isSingleStoreMode = singleStoreId !== undefined;
  
  const [selectedStoreId, setSelectedStoreId] = useState<string>(
    singleStoreId?.toString() || ''
  );
  const [query, setQuery] = useState('');
  const [k, setK] = useState(DEFAULT_RETRIEVAL_K);
  const [results, setResults] = useState<RetrievedChunk[]>([]);

  const retrieveChunks = useRetrieveChunks();

  const handleRetrieve = async () => {
    const currentStoreId = isSingleStoreMode ? singleStoreId : Number.parseInt(selectedStoreId, 10);
    
    if (!currentStoreId || !query.trim()) return;

    try {
      const response = await retrieveChunks.mutateAsync({
        storeId: currentStoreId,
        request: { query, k },
      });
      setResults(response.chunks);
    } catch (error) {
      handleError(error, ...ERROR_TEMPLATES.RETRIEVAL_QUERY(currentStoreId, query));
      setResults([]);
    }
  };

  // Don't render if multi-store mode but no stores provided
  if (!isSingleStoreMode && stores.length === 0) {
    return null;
  }

  const defaultDescription = isSingleStoreMode
    ? 'Search this store to test document retrieval'
    : 'Search any active store to test document retrieval';

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {storeName ? `${title}: ${storeName}` : title}
          </CardTitle>
          <CardDescription>{description || defaultDescription}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-4 md:flex-row">
            {/* Store selector (multi-store mode only) */}
            {!isSingleStoreMode && (
              <Select
                value={selectedStoreId}
                onValueChange={setSelectedStoreId}
              >
                <SelectTrigger className="md:w-[200px]">
                  <SelectValue placeholder="Select a store" />
                </SelectTrigger>
                <SelectContent>
                  {stores.map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {/* Query input */}
            <Input
              placeholder="Enter your search query..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRetrieve()}
              className="flex-1"
            />

            {/* K parameter */}
            <Input
              type="number"
              min={MIN_RETRIEVAL_K}
              max={MAX_RETRIEVAL_K}
              value={k}
              onChange={(e) => setK(Number.parseInt(e.target.value) || DEFAULT_RETRIEVAL_K)}
              className="w-20"
              title="Number of results (k)"
            />

            {/* Search button */}
            <Button 
              onClick={handleRetrieve} 
              disabled={
                retrieveChunks.isPending || 
                !query.trim() || 
                (!isSingleStoreMode && !selectedStoreId)
              }
            >
              {retrieveChunks.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </>
              )}
            </Button>
          </div>

          {retrieveChunks.isError && (
            <IconLabel icon={<AlertCircle className="h-4 w-4" />} gap="sm" className="text-sm text-destructive">
              Failed to retrieve documents
            </IconLabel>
          )}
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            Results ({results.length} chunks)
          </h3>
          <RetrievalResults chunks={results} />
        </div>
      )}
    </div>
  );
}
