import { useState } from 'react';
import { useDocuments } from '@/hooks/useVectorStores';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { IconLabel } from '@/components/ui/icon-label';
import { AlertCircle, FileText, Edit2, Trash2, Loader2 } from 'lucide-react';
import { EditDocumentDialog } from './EditDocumentDialog';
import { DeleteDocumentDialog } from './DeleteDocumentDialog';
import type { Document } from '@/types/vectorStore';

interface DocumentListProps {
  readonly storeId: number;
}

export function DocumentList({ storeId }: Readonly<DocumentListProps>) {
  const { data: documents, isLoading, error } = useDocuments(storeId);

  const [editDocument, setEditDocument] = useState<Document | null>(null);
  const [deleteDocument, setDeleteDocument] = useState<Document | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="py-6">
          <IconLabel icon={<AlertCircle className="h-5 w-5 text-destructive" />} gap="md">
            <p className="text-sm">Failed to load documents. Please try again.</p>
          </IconLabel>
        </CardContent>
      </Card>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/25 p-8 text-center">
        <FileText className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-sm text-muted-foreground">
          No documents uploaded yet. Upload a document to get started.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="rounded-lg border">
        <table className="w-full">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Filename</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Type</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Size</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Chunks</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className="border-b last:border-b-0 hover:bg-muted/30">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{doc.filename}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-muted-foreground">{doc.file_type}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm text-muted-foreground">
                    {((doc.file_size ?? 0) / 1024).toFixed(2)} KB
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-sm text-muted-foreground">{doc.chunk_count}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setEditDocument(doc)}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDeleteDocument(doc)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editDocument && (
        <EditDocumentDialog
          storeId={storeId}
          docId={editDocument.id}
          open={!!editDocument}
          onClose={() => setEditDocument(null)}
        />
      )}

      {deleteDocument && (
        <DeleteDocumentDialog
          storeId={storeId}
          document={deleteDocument}
          open={!!deleteDocument}
          onClose={() => setDeleteDocument(null)}
        />
      )}
    </>
  );
}
