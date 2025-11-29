import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Search } from 'lucide-react';
import { ScoreBadge } from './ScoreBadge';
import type { RetrievedChunk } from '@/types/vectorStore';

interface RetrievalResultsProps {
  chunks: RetrievedChunk[];
  emptyMessage?: string;
}

/**
 * Displays a list of retrieved document chunks with their similarity scores.
 */
export function RetrievalResults({ 
  chunks, 
  emptyMessage = 'No results found' 
}: Readonly<RetrievalResultsProps>) {
  if (chunks.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {chunks.map((chunk, index) => (
        <Card key={`chunk-${chunk.score}-${index}`} className="overflow-hidden">
          <CardHeader className="py-2 px-4 bg-muted/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Chunk {index + 1}</span>
              <ScoreBadge score={chunk.score} />
            </div>
          </CardHeader>
          <CardContent className="p-4">
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{chunk.content}</p>
            {Object.keys(chunk.metadata).length > 0 && (
              <div className="mt-2 pt-2 border-t">
                <p className="text-xs text-muted-foreground font-mono">
                  {JSON.stringify(chunk.metadata, null, 2)}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
