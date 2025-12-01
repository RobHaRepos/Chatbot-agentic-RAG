import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { logger } from '@/services/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * FIXED: Now logs errors to backend logger service for production monitoring
 * Error Boundary to catch React errors and prevent full app crashes
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // FIXED: Send to logger service for production monitoring
    logger.log('error', 'unhandled_react_error', {
      message: error.message,
      stack: error.stack || 'No stack trace',
      componentStack: errorInfo.componentStack || 'No component stack',
      errorName: error.name,
    });
  }

  private readonly handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-screen p-4">
          <Card className="max-w-md w-full border-destructive">
            <CardHeader>
              <IconLabel icon={<AlertCircle className="h-8 w-8 text-destructive" />} gap="md">
                <div>
                  <CardTitle>Something went wrong</CardTitle>
                  <CardDescription>
                    The application encountered an unexpected error
                  </CardDescription>
                </div>
              </IconLabel>
            </CardHeader>
            <CardContent className="space-y-4">
              {this.state.error && (
                <details className="text-sm bg-muted p-3 rounded-md">
                  <summary className="cursor-pointer font-medium mb-2">
                    Error details
                  </summary>
                  <pre className="text-xs overflow-auto">
                    {this.state.error.message}
                  </pre>
                </details>
              )}
              <div className="flex gap-2">
                <Button onClick={this.handleReset} className="flex-1">
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={() => globalThis.location.href = '/'}
                  className="flex-1"
                >
                  Go Home
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
