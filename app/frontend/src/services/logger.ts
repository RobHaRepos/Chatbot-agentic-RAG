type LogLevel = 'info' | 'error' | 'warn';

interface LogMeta {
  [key: string]: unknown;
}

class FrontendLogger {
  log(level: LogLevel, event: string, meta?: LogMeta): void {
    // Determine console method
    let consoleMethod: 'log' | 'error' | 'warn' = 'log';
    if (level === 'error') {
      consoleMethod = 'error';
    } else if (level === 'warn') {
      consoleMethod = 'warn';
    }

    // Console logging
    console[consoleMethod](
      `[${level.toUpperCase()}] ${event}`,
      meta || ''
    );

    // You can extend this to send logs to a backend service
    // For now, we'll just console log
  }
}

export const logger = new FrontendLogger();

// Make it globally available (for backward compatibility)
if (globalThis.window !== undefined) {
  (globalThis as unknown as { FrontendLogger: FrontendLogger }).FrontendLogger = logger;
}
