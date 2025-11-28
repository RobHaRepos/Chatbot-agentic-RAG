import * as React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  readonly value: string;
  readonly label: string;
  readonly group?: string;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  readonly options: readonly SelectOption[];
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly placeholder?: string;
  readonly groupBy?: boolean;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, value, onChange, placeholder, groupBy = false, ...props }, ref) => {
    // Group options if groupBy is true
    const groupedOptions = React.useMemo(() => {
      if (!groupBy) return null;
      
      const groups: Record<string, SelectOption[]> = {};
      for (const option of options) {
        const group = option.group || 'Other';
        if (!groups[group]) groups[group] = [];
        groups[group].push(option);
      }
      return groups;
    }, [options, groupBy]);

    return (
      <div className="relative">
        <select
          ref={ref}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            'flex h-10 w-full appearance-none rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm ring-offset-background',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            className
          )}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {groupBy && groupedOptions ? (
            Object.entries(groupedOptions).map(([group, groupOptions]) => (
              <optgroup key={group} label={group}>
                {groupOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </optgroup>
            ))
          ) : (
            options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))
          )}
        </select>
        <ChevronDown 
          className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" 
          aria-hidden="true" 
        />
      </div>
    );
  }
);

Select.displayName = 'Select';

export { Select };
