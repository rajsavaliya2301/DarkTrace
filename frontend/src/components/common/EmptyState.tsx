import { cn } from '../../utils/cn';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  icon?: React.ReactNode;
  className?: string;
}

export default function EmptyState({
  title = 'No data found',
  message = 'There are no items to display at the moment.',
  action,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed border-dark-border p-8 text-center',
        className
      )}
    >
      <div className="mb-4 text-gray-600">
        {icon || <Inbox className="h-12 w-12" />}
      </div>
      <h3 className="mb-2 text-lg font-medium text-gray-300">{title}</h3>
      <p className="mb-6 max-w-md text-sm text-gray-500">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
