import { cn } from '@/lib/utils';

/**
 * Skeleton placeholder component for loading states
 * Provides better UX than plain "Loading..." text
 */
function Skeleton({
  className,
  ...props
}: Readonly<React.HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-muted', className)}
      {...props}
    />
  );
}

export { Skeleton };
