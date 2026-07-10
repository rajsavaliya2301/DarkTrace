import { useParams } from 'react-router-dom';
import { useActorDetail } from '../hooks/useActors';
import ActorDetailView from '../components/actors/ActorDetail';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';
import { toast } from 'react-hot-toast';

export default function ActorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, refetch } = useActorDetail(id || '');

  // Real-time updates for this specific actor
  useRealtimeUpdates({
    channels: 'actor',
    onActor: (event) => {
      // Refetch when this actor is updated
      if (event.actor_id === id) {
        refetch();
      }
      // Show notification when new content is linked
      if (event.actor_id === id && event.action === 'content_linked') {
        toast(`📎 New content linked to this actor`, {
          duration: 3000,
          style: { background: '#1f2937', color: '#f9fafb' },
        });
      }
    },
  });

  return (
    <ActorDetailView
      data={data}
      isLoading={isLoading}
      isError={isError}
      onRetry={() => refetch()}
    />
  );
}
