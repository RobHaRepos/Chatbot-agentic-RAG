import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Loader2, AlertCircle } from 'lucide-react';
import { RetrievalResults } from './RetrievalResults';
import { retrieveFromStore } from '@/services/retrieverApi';
import type { RetrievedChunk } from '@/types/vectorStore';

interface RetrievalTestPanelProps {
  storeId: number;
  storeName?: string;
  title?: string;
  description?: string;
}

/**
 * A reusable panel for testing document retrieval against a vector store.
 * Includes query input, k parameter, and results display.
 */
export function RetrievalTestPanel({
  storeId,
  storeName,
  title = 'Test Retrieval',
  description = 'Search this store to test document retrieval',
}: Readonly<RetrievalTestPanelProps>) {
  const [query, setQuery] = useState('');
  const [k, setK] = useState(5);
  const [retrieving, setRetrieving] = useState(false);
  const [results, setResults] = useState<RetrievedChunk[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleRetrieve = async () => {
    if (!query.trim()) return;

    try {
      setRetrieving(true);
      setError(null);
      const response = await retrieveFromStore(storeId, { query, k });
      setResults(response.chunks);
    } catch {
      setError('Failed to retrieve documents');
    } finally {
      setRetrieving(false);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {storeName ? `${title}: ${storeName}` : title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter your search query..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRetrieve()}
              className="flex-1"
            />
            <Input
              type="number"
              min={1}
              max={20}
              value={k}
              onChange={(e) => setK(Number.parseInt(e.target.value) || 5)}
              className="w-20"
              title="Number of results (k)"
            />
            <Button onClick={handleRetrieve} disabled={retrieving || !query.trim()}>
              {retrieving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Search
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
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
