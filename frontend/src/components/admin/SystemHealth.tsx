import { cn } from '../../utils/cn';
import { CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react';
import LoadingSpinner from '../common/LoadingSpinner';
import type { SystemHealthResponse } from '../../types';

interface SystemHealthProps {
  data: SystemHealthResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

const statusIcon = (status: string) => {
  switch (status) {
    case 'up':
      return <CheckCircle className="h-5 w-5 text-emerald-400" />;
    case 'degraded':
      return <AlertTriangle className="h-5 w-5 text-amber-400" />;
    case 'down':
      return <XCircle className="h-5 w-5 text-red-400" />;
    default:
      return <Activity className="h-5 w-5 text-gray-400" />;
  }
};

const statusBg = (status: string) => {
  switch (status) {
    case 'up':
      return 'border-emerald-500/20 bg-emerald-500/5';
    case 'degraded':
      return 'border-amber-500/20 bg-amber-500/5';
    case 'down':
      return 'border-red-500/20 bg-red-500/5';
    default:
      return 'border-dark-border bg-dark-card';
  }
};

export default function SystemHealth({
  data,
  isLoading,
  isError,
}: SystemHealthProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <LoadingSpinner size="lg" label="Loading system health..." />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-8 text-center">
        <p className="text-red-400">Failed to load system health data</p>
      </div>
    );
  }

  const services = Object.entries(data.services);

  return (
    <div className="space-y-4">
      <div
        className={cn(
          'flex items-center gap-3 rounded-xl border p-4',
          data.status === 'healthy'
            ? 'border-emerald-500/20 bg-emerald-500/5'
            : 'border-amber-500/20 bg-amber-500/5'
        )}
      >
        {statusIcon(data.status === 'healthy' ? 'up' : 'degraded')}
        <div>
          <p className="text-sm font-medium text-gray-200 capitalize">
            System Status: {data.status}
          </p>
          <p className="text-xs text-gray-500">
            All systems are operational
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {services.map(([name, service]) => (
          <div
            key={name}
            className={cn(
              'rounded-xl border p-4',
              statusBg(service.status)
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {statusIcon(service.status)}
                <span className="text-sm font-medium text-gray-200 capitalize">
                  {name.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
            <div className="mt-3 space-y-1 text-xs text-gray-400">
              {service.uptime && (
                <p>Uptime: {service.uptime}</p>
              )}
              {service.workers !== undefined && (
                <p>Workers: {service.workers}</p>
              )}
              {service.queue_depth !== undefined && (
                <p>Queue Depth: {service.queue_depth}</p>
              )}
              {service.throughput && (
                <p>Throughput: {service.throughput}</p>
              )}
              {service.message && (
                <p className="text-amber-400">{service.message}</p>
              )}
              {service.health && (
                <p>
                  Health:{' '}
                  <span
                    className={cn(
                      service.health === 'green'
                        ? 'text-emerald-400'
                        : service.health === 'yellow'
                          ? 'text-amber-400'
                          : 'text-red-400'
                    )}
                  >
                    {service.health}
                  </span>
                </p>
              )}
              {service.queues !== undefined && (
                <p>Queues: {service.queues}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
