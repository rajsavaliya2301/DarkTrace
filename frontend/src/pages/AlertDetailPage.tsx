import { useParams } from 'react-router-dom';
import { useAlertDetail } from '../hooks/useAlerts';
import AlertDetailView from '../components/alerts/AlertDetail';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';
import { toast } from 'react-hot-toast';

export default function AlertDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, refetch } = useAlertDetail(id || '');

  // Real-time updates for this specific alert
  useRealtimeUpdates({
    channels: 'alert',
    onAlert: (event) => {
      // Refetch when this alert is updated
      if (event.alert_id === id) {
        refetch();
      }
      // Show notification when severity changes
      if (event.alert_id === id && event.action === 'severity_changed') {
        toast(`⚠️ Alert severity changed to ${event.severity}`, {
          duration: 4000,
          style: { background: '#1f2937', color: '#f9fafb' },
        });
      }
    },
  });

  return (
    <AlertDetailView
      data={data}
      isLoading={isLoading}
      isError={isError}
      onRetry={() => refetch()}
    />
  );
}
