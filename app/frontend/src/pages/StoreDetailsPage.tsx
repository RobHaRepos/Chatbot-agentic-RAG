import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Database, ArrowLeft, FileText, Cpu, Hash } from 'lucide-react';
import { LoadingState, ErrorState } from '@/components/common';
import { RetrievalTestPanel } from '@/components/retrieval';
import { getStore } from '@/services/retrieverApi';
import type { VectorStore } from '@/types/vectorStore';

export function StoreDetailsPage() {
  const { storeId } = useParams<{ storeId: string }>();
  const navigate = useNavigate();

  const [store, setStore] = useState<VectorStore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (storeId) {
      loadStore(Number.parseInt(storeId));
    }
  }, [storeId]);

  const loadStore = async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getStore(id);
      setStore(data);
    } catch {
      setError('Failed to load store details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingState message="Loading store details..." />
      </div>
    );
  }

  if (error || !store) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <ErrorState
          message={error || 'Store not found'}
          onRetry={storeId ? () => loadStore(Number.parseInt(storeId)) : undefined}
        />
        <Button variant="outline" onClick={() => navigate('/vectorstores')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Stores
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-6 py-4">
        <div className="max-w-6xl mx-auto">
          <Button
            variant="ghost"
            size="sm"
            className="mb-2"
            onClick={() => navigate('/vectorstores')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Stores
          </Button>
          <div className="flex items-center gap-3">
            <Database className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">{store.name}</h1>
              {store.description && (
                <p className="text-sm text-muted-foreground">{store.description}</p>
              )}
            </div>
            <Badge variant={store.is_active ? 'default' : 'secondary'} className="ml-auto">
              {store.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Store Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{store.document_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Hash className="h-4 w-4" />
                  Chunks
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{store.chunk_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Cpu className="h-4 w-4" />
                  Embedding Model
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
        </div>
      </div>
    </div>
  );
}
