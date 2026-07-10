import { cn } from '../../utils/cn';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

export default function LoadingSpinner({ size = 'md', className, label }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
  };

  return (
    <div
      className={cn('flex flex-col items-center justify-center gap-3', className)}
      role="status"
      aria-label={label || 'Loading'}
    >
      <div
        className={cn(
          'animate-spin rounded-full border-dark-border border-t-blue-500',
          sizeClasses[size]
        )}
      />
      {label && <p className="text-sm text-gray-400">{label}</p>}
    </div>
  );
}
