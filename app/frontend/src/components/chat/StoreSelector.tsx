import { useState, useEffect } from 'react';
import { Database, AlertCircle, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getStores } from '@/services/retrieverApi';
import { useChatStore } from '@/store/chatStore';
import type { VectorStore } from '@/types/vectorStore';

export function StoreSelector() {
  const [stores, setStores] = useState<VectorStore[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  
  const { selectedStoreId, setSelectedStoreId } = useChatStore();
  
  const selectedStore = stores.find(s => s.id === selectedStoreId);

  useEffect(() => {
    loadStores();
  }, []);

  const loadStores = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getStores();
      setStores(data);
      // Auto-select first active store if none selected
      if (!selectedStoreId && data.length > 0) {
        const activeStore = data.find(s => s.is_active) || data[0];
        setSelectedStoreId(activeStore.id);
      }
    } catch {
      setError('Failed to load stores');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Database className="h-4 w-4 animate-pulse" />
        <span>Loading stores...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-sm text-destructive">
        <AlertCircle className="h-4 w-4" />
        <span>{error}</span>
        <Button variant="ghost" size="sm" onClick={loadStores}>
          Retry
        </Button>
      </div>
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
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2"
      >
        <Database className="h-4 w-4" />
        <span className="max-w-[150px] truncate">
          {selectedStore?.name || 'Select store'}
        </span>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>
      
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)} 
          />
          
          {/* Dropdown */}
          <div className="absolute top-full mt-1 left-0 z-20 w-64 bg-popover border border-border rounded-md shadow-lg overflow-hidden">
            <div className="max-h-60 overflow-y-auto">
              {stores.map((store) => (
                <button
                  key={store.id}
                  onClick={() => {
                    setSelectedStoreId(store.id);
                    setIsOpen(false);
                  }}
                  className={`w-full px-3 py-2 text-left hover:bg-accent transition-colors ${
                    store.id === selectedStoreId ? 'bg-accent' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm truncate">{store.name}</span>
                    {!store.is_active && (
                      <span className="text-xs text-muted-foreground">(inactive)</span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {store.document_count} docs • {store.chunk_count} chunks
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
