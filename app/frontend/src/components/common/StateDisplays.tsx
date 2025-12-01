import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: Readonly<ErrorStateProps>) {
  return (
    <Card className="border-destructive">
      <CardContent className="py-6">
        <IconLabel icon={<AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />} gap="md">
          <p className="text-sm flex-1">{message}</p>
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              Retry
            </Button>
          )}
        </IconLabel>
      </CardContent>
    </Card>
  );
}

interface EmptyStateProps {
  icon: React.ReactNode;
  message: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, message, action }: Readonly<EmptyStateProps>) {
  return (
    <Card>
      <CardContent className="py-8 text-center text-muted-foreground">
        <div className="mx-auto mb-3 opacity-50">{icon}</div>
        <p className="text-sm">{message}</p>
        {action && <div className="mt-4">{action}</div>}
      </CardContent>
    </Card>
  );
}
