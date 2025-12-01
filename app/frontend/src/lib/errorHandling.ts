import { toast } from '@/hooks/useToast';
import { logger } from '@/services/logger';

interface ErrorOptions {
  /**
   * Error title to display in toast
   */
  title?: string;
  /**
   * Whether to log the error to the logger service
   */
  log?: boolean;
  /**
   * Additional context for logging
   */
  context?: Record<string, unknown>;
}

/**
 * Centralized error handling function.
 * Displays toast notification and optionally logs to backend.
 * 
 * CRITICAL: This replaces all console.error() and alert() patterns.
 */
export function handleError(
  error: unknown,
  defaultMessage: string = 'An unexpected error occurred',
  options: ErrorOptions = {}
): void {
  const { title = 'Error', log = true, context = {} } = options;

  // Extract error message
  let message = defaultMessage;
  if (error instanceof Error) {
    message = error.message || defaultMessage;
  } else if (typeof error === 'string') {
    message = error;
  }

  // Display toast notification
  toast({
    title,
    description: message,
    variant: 'destructive',
  });

  // Log to service
  if (log) {
    logger.log('error', 'error_occurred', {
      message,
      error: error instanceof Error ? error.stack : String(error),
      ...context,
    });
  }
}

/**
 * Display a success toast notification
 */
export function showSuccess(
  title: string,
  description?: string
): void {
  toast({
    title,
    description,
    variant: 'success',
  });
}

/**
 * Display an error toast notification without logging
 * Use for validation errors or user-facing messages
 */
export function showError(
  description: string,
  options: { title?: string } = {}
): void {
  const { title = 'Error' } = options;
  toast({
    title,
    description,
    variant: 'destructive',
  });
}

/**
 * Display an info toast notification
 */
export function showInfo(
  title: string,
  description?: string
): void {
  toast({
    title,
    description,
    variant: 'default',
  });
}

/**
 * Extract error message from various error types
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'An unexpected error occurred';
}
