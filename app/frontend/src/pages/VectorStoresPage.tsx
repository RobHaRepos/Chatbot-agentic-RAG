import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, Plus } from 'lucide-react';

export function VectorStoresPage() {
  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold">Vector Stores</h1>
            <p className="text-sm text-muted-foreground">
              Manage your document vector stores
            </p>
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create Store
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          {/* Placeholder content */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                  <Database className="h-6 w-6" />
                </div>
                <div>
                  <CardTitle>Vector Store Management</CardTitle>
                  <CardDescription>Coming Soon</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                This page will allow you to:
              </p>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li>• Create new vector stores from documents</li>
                <li>• List and manage existing vector stores</li>
                <li>• Switch between FAISS and PostgreSQL pgvector</li>
                <li>• Add or remove documents from stores</li>
                <li>• View store statistics and metadata</li>
              </ul>
              <div className="mt-6 p-4 rounded-lg bg-muted/30">
                <p className="text-xs text-muted-foreground">
                  <strong>Note:</strong> Backend API endpoints need to be implemented in the retriever service first.
                  Once the endpoints are ready, this UI will be connected to provide full vector store management capabilities.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
