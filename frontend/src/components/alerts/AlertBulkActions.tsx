import { useState } from 'react';
import { Check, X } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useBulkAlertUpdate } from '../../hooks/useAlerts';
import ConfirmDialog from '../common/ConfirmDialog';

interface AlertBulkActionsProps {
  selectedIds: Set<string>;
  onClear: () => void;
}

type BulkAction = 'acknowledge' | 'investigating' | 'resolved' | 'dismiss';

export default function AlertBulkActions({
  selectedIds,
  onClear,
}: AlertBulkActionsProps) {
  const [confirmAction, setConfirmAction] = useState<BulkAction | null>(null);
  const bulkUpdate = useBulkAlertUpdate();
  const count = selectedIds.size;

  const handleBulkAction = (action: BulkAction) => {
    setConfirmAction(action);
  };

  const confirmHandler = () => {
    if (!confirmAction) return;
    bulkUpdate.mutate(
      {
        alert_ids: Array.from(selectedIds),
        action: confirmAction,
      },
      {
        onSuccess: () => {
          onClear();
          setConfirmAction(null);
        },
      }
    );
  };

  if (count === 0) return null;

  const actionLabels: Record<BulkAction, string> = {
    acknowledge: 'Acknowledge',
    investigating: 'Mark Investigating',
    resolved: 'Resolve',
    dismiss: 'Dismiss',
  };

  const actionColors: Record<BulkAction, string> = {
    acknowledge: 'bg-blue-600 hover:bg-blue-700',
    investigating: 'bg-amber-600 hover:bg-amber-700',
    resolved: 'bg-emerald-600 hover:bg-emerald-700',
    dismiss: 'bg-gray-600 hover:bg-gray-700',
  };

  return (
    <>
      <div className="flex items-center gap-3 rounded-lg border border-blue-500/30 bg-blue-500/5 px-4 py-3">
        <span className="text-sm text-gray-300">
          <strong className="text-white">{count}</strong> alert{count > 1 ? 's' : ''} selected
        </span>
        <div className="flex items-center gap-2">
          {(Object.keys(actionLabels) as BulkAction[]).map((action) => (
            <button
              key={action}
              onClick={() => handleBulkAction(action)}
              disabled={bulkUpdate.isPending}
              className={cn(
                'rounded-md px-3 py-1.5 text-xs font-medium text-white transition-colors disabled:opacity-50',
                actionColors[action]
              )}
            >
              {actionLabels[action]}
            </button>
          ))}
        </div>
        <button
          onClick={onClear}
          className="ml-auto rounded p-1 text-gray-500 hover:text-gray-300"
          aria-label="Clear selection"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <ConfirmDialog
        isOpen={!!confirmAction}
        onClose={() => setConfirmAction(null)}
        onConfirm={confirmHandler}
        title={`${actionLabels[confirmAction || 'acknowledge']} Alerts`}
        message={`Are you sure you want to ${confirmAction} ${count} alert${count > 1 ? 's' : ''}?`}
        variant={confirmAction === 'dismiss' ? 'warning' : 'info'}
        confirmLabel={actionLabels[confirmAction || 'acknowledge']}
        isLoading={bulkUpdate.isPending}
      />
    </>
  );
}
