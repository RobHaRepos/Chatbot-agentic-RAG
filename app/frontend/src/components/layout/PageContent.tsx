import type { ReactNode } from 'react';

interface PageContentProps {
  children: ReactNode;
  className?: string;
}

/**
 * Reusable page content wrapper with consistent max-width and padding.
 */
export function PageContent({ children, className = '' }: Readonly<PageContentProps>) {
  return (
    <div className={`flex-1 overflow-y-auto p-4 md:p-6 ${className}`}>
      <div className="max-w-6xl mx-auto space-y-6">
        {children}
      </div>
    </div>
  );
}
