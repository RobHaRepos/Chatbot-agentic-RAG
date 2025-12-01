import { memo, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

type GapSize = 'xs' | 'sm' | 'md' | 'lg';

interface IconLabelProps {
  readonly icon: ReactNode;
  readonly children: ReactNode;
  readonly gap?: GapSize;
  readonly className?: string;
}

/**
 * CRITICAL FIX: Eliminates 28+ duplicate "flex items-center gap-X" patterns
 * Reusable component for icon + label layouts
 * 
 * Usage:
 *   <IconLabel icon={<Icon />} gap="sm">Label</IconLabel>
 */
export const IconLabel = memo(function IconLabel({
  icon,
  children,
  gap = 'sm',
  className,
}: IconLabelProps) {
  const gapClass = {
    xs: 'gap-1',
    sm: 'gap-2',
    md: 'gap-3',
    lg: 'gap-4',
  }[gap];

  return (
    <div className={cn('flex items-center', gapClass, className)}>
      {icon}
      {children}
    </div>
  );
});
