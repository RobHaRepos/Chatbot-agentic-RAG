import * as React from 'react';
import { cn } from '@/lib/utils';

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  readonly value: number;
  readonly onChange: (value: number) => void;
  readonly min?: number;
  readonly max?: number;
  readonly step?: number;
  readonly showValue?: boolean;
  readonly formatValue?: (value: number) => string;
}

const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  (
    {
      className,
      value,
      onChange,
      min = 0,
      max = 100,
      step = 1,
      showValue = true,
      formatValue = (v) => v.toString(),
      ...props
    },
    ref
  ) => {
    // Calculate percentage for gradient background
    const percentage = ((value - min) / (max - min)) * 100;

    return (
      <div className="flex items-center gap-3 w-full">
        <input
          ref={ref}
          type="range"
          value={value}
          onChange={(e) => onChange(Number.parseFloat(e.target.value))}
          min={min}
          max={max}
          step={step}
          className={cn(
            'w-full h-2 rounded-full appearance-none cursor-pointer',
            'bg-muted',
            '[&::-webkit-slider-thumb]:appearance-none',
            '[&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5',
            '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary',
            '[&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-background',
            '[&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-110',
            '[&::-webkit-slider-thumb]:active:scale-95',
            '[&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:w-5',
            '[&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary',
            '[&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-background',
            '[&::-moz-range-thumb]:shadow-md',
            'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            className
          )}
          style={{
            background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${percentage}%, hsl(var(--muted)) ${percentage}%, hsl(var(--muted)) 100%)`,
          }}
          {...props}
        />
        {showValue && (
          <span className="min-w-[3rem] text-sm font-medium text-muted-foreground text-right">
            {formatValue(value)}
          </span>
        )}
      </div>
    );
  }
);

Slider.displayName = 'Slider';

export { Slider };
