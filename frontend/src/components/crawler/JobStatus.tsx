import { cn } from '../../utils/cn';
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import type { CrawlJobStatus } from '../../utils/constants';

interface JobStatusProps {
  status: CrawlJobStatus | string;
  size?: 'sm' | 'md';
  showLabel?: boolean;
}

const config: Record<
  string,
  { icon: React.ElementType; label: string; color: string }
> = {
  queued: {
    icon: Clock,
    label: 'Queued',
    color: 'text-gray-400',
  },
  in_progress: {
    icon: Loader2,
    label: 'In Progress',
    color: 'text-blue-400',
  },
  completed: {
    icon: CheckCircle,
    label: 'Completed',
    color: 'text-emerald-400',
  },
  failed: {
    icon: XCircle,
    label: 'Failed',
    color: 'text-red-400',
  },
};

export default function JobStatus({
  status,
  size = 'sm',
  showLabel = true,
}: JobStatusProps) {
  const cfg = config[status] || config.queued;
  const Icon = cfg.icon;
  const iconSize = size === 'sm' ? 'h-3.5 w-3.5' : 'h-5 w-5';

  return (
    <span className={cn('inline-flex items-center gap-1.5', cfg.color)}>
      <Icon
        className={cn(
          iconSize,
          status === 'in_progress' && 'animate-spin'
        )}
      />
      {showLabel && (
        <span className={cn(size === 'sm' ? 'text-xs' : 'text-sm')}>
          {cfg.label}
        </span>
      )}
    </span>
  );
}
