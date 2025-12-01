import { memo, type ReactNode } from 'react';
import { IconLabel } from '@/components/ui/icon-label';

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  backButton?: ReactNode;
  icon?: ReactNode;
}

/**
 * Reusable page header component with consistent styling across pages.
 * Supports title, description, action buttons, back navigation, and icons.
 * FIXED: Memoized for consistency with other UI components.
 */
export const PageHeader = memo(function PageHeader({
  title,
  description,
  actions,
  backButton,
  icon,
}: Readonly<PageHeaderProps>) {
  return (
    <div className="border-b border-border bg-card/30 backdrop-blur-sm px-4 md:px-6 py-3 md:py-4">
      <div className="max-w-6xl mx-auto">
        {backButton && <div className="mb-2">{backButton}</div>}
        <div className="flex items-center justify-between gap-2">
          {icon ? (
            <IconLabel icon={icon} gap="md" className="min-w-0 flex-1">
              <div>
                <h1 className="text-xl md:text-2xl font-bold">{title}</h1>
                {description && (
                  <p className="text-xs md:text-sm text-muted-foreground">
                    {description}
                  </p>
                )}
              </div>
            </IconLabel>
          ) : (
            <div className="min-w-0 flex-1">
              <h1 className="text-xl md:text-2xl font-bold">{title}</h1>
              {description && (
                <p className="text-xs md:text-sm text-muted-foreground">
                  {description}
                </p>
              )}
            </div>
          )}
          {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
      </div>
    </div>
  );
});
