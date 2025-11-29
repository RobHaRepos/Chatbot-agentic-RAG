import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Database, Search, Loader2, AlertCircle, CheckCircle2, ChevronRight } from 'lucide-react';
import { LoadingState, ErrorState, EmptyState } from '@/components/common';
import { StoreCard } from '@/components/stores';
import { RetrievalResults } from '@/components/retrieval';
import { getStores, retrieveFromStore } from '@/services/retrieverApi';
import type { VectorStore, RetrievedChunk } from '@/types/vectorStore';

function StoresContent({
  loading,
  error,
  stores,
  selectedStore,
  setSelectedStore,
  setResults,
  loadStores,
  query,
  setQuery,
  k,
  setK,
  retrieving,
  results,
  retrievalError,
  handleRetrieve,
  onViewDetails,
}: Readonly<{
  loading: boolean;
  error: string | null;
  stores: VectorStore[];
  selectedStore: VectorStore | null;
  setSelectedStore: (store: VectorStore) => void;
  setResults: (results: RetrievedChunk[]) => void;
  loadStores: () => void;
  query: string;
  setQuery: (query: string) => void;
  k: number;
  setK: (k: number) => void;
  retrieving: boolean;
  results: RetrievedChunk[];
  retrievalError: string | null;
  handleRetrieve: () => void;
  onViewDetails: (storeId: number) => void;
}>) {
  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadStores} />;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Stores List */}
      <div className="space-y-4">
        <h2 className="text-sm font-medium text-muted-foreground">
          Available Stores ({stores.length})
        </h2>
        {stores.length === 0 ? (
          <EmptyState
            icon={<Database className="h-8 w-8" />}
            message="No vector stores yet"
          />
        ) : (
          <div className="space-y-2">
            {stores.map((store) => (
              <StoreCard
                key={store.id}
                store={store}
                isSelected={selectedStore?.id === store.id}
                onSelect={() => {
                  setSelectedStore(store);
                  setResults([]);
                }}
                onViewDetails={() => onViewDetails(store.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Query & Results */}
      <div className="lg:col-span-2 space-y-4">
        {selectedStore ? (
          <>
            {/* Selected Store Info */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <CardTitle className="text-base">
                    Querying: {selectedStore.name}
                  </CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Query Input */}
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
                    title="Number of results"
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

                {retrievalError && (
                  <div className="flex items-center gap-2 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4" />
                    {retrievalError}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Results */}
            {results.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-3">
                  Results ({results.length} chunks)
                </h3>
                <RetrievalResults chunks={results} />
              </div>
            )}
          </>
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <ChevronRight className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Select a store to start querying</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export function VectorStoresPage() {
  const navigate = useNavigate();
  const [stores, setStores] = useState<VectorStore[]>([]);
  const [selectedStore, setSelectedStore] = useState<VectorStore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Retrieval state
  const [query, setQuery] = useState('');
  const [k, setK] = useState(5);
  const [retrieving, setRetrieving] = useState(false);
  const [results, setResults] = useState<RetrievedChunk[]>([]);
  const [retrievalError, setRetrievalError] = useState<string | null>(null);

  const loadStores = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getStores();
      setStores(data);
      if (data.length > 0 && !selectedStore) {
        setSelectedStore(data[0]);
      }
    } catch (err) {
      setError('Failed to load vector stores. Is the retriever service running?');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetrieve = async () => {
    if (!selectedStore || !query.trim()) return;
    
    try {
      setRetrieving(true);
      setRetrievalError(null);
      const response = await retrieveFromStore(selectedStore.id, { query, k });
      setResults(response.chunks);
    } catch (err) {
      setRetrievalError('Failed to retrieve documents');
      console.error(err);
    } finally {
      setRetrieving(false);
    }
  };

  useEffect(() => {
    loadStores();
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold">Vector Stores</h1>
            <p className="text-sm text-muted-foreground">
              Manage and query your document vector stores
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          <StoresContent
            loading={loading}
            error={error}
            stores={stores}
            selectedStore={selectedStore}
            setSelectedStore={setSelectedStore}
            setResults={setResults}
            loadStores={loadStores}
            query={query}
            setQuery={setQuery}
            k={k}
            setK={setK}
            retrieving={retrieving}
            results={results}
            retrievalError={retrievalError}
            handleRetrieve={handleRetrieve}
            onViewDetails={(storeId) => navigate(`/vectorstores/${storeId}`)}
          />
        </div>
      </div>
    </div>
  );
}
