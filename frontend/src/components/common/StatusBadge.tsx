import { cn } from '../../utils/cn';
import {
  SEVERITY_BG_CLASSES,
  type SeverityLevel,
} from '../../utils/constants';
import { capitalize } from '../../utils/formatters';

interface StatusBadgeProps {
  severity: SeverityLevel;
  className?: string;
  size?: 'sm' | 'md';
}

export default function StatusBadge({
  severity,
  className,
  size = 'sm',
}: StatusBadgeProps) {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        SEVERITY_BG_CLASSES[severity] || SEVERITY_BG_CLASSES.info,
        sizeClasses,
        className
      )}
    >
      {capitalize(severity)}
    </span>
  );
}
