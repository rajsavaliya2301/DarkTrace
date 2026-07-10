import { useState, useEffect, useRef } from 'react';
import { WS_BASE_URL, API_BASE_URL } from '../../utils/constants';
import { cn } from '../../utils/cn';

type ConnectionState = 'connecting' | 'connected' | 'polling' | 'disconnected';

/**
 * Small badge showing real-time connection status.
 * Uses the /events/poll endpoint as a health check.
 */
export default function ConnectionStatus() {
  const [state, setState] = useState<ConnectionState>('connecting');
  const [showTooltip, setShowTooltip] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Try WebSocket connection to gauge status
    const wsBase = WS_BASE_URL.replace('/v1', '').replace(/\/+$/, '');
    const wsUrl = `${wsBase}/ws/events?channels=dashboard`;

    const connectWs = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => setState('connected');
        ws.onclose = () => {
          setState('polling');
          wsRef.current = null;
        };
        ws.onerror = () => {
          setState('polling');
          wsRef.current?.close();
          wsRef.current = null;
        };
      } catch {
        setState('polling');
      }
    };

    // If WebSocket fails, verify polling works
    const checkPolling = async () => {
      try {
        const apiBase = API_BASE_URL.replace(/\/+$/, '');
        const res = await fetch(`${apiBase}/events/poll?channel=dashboard&limit=1`, {
          signal: AbortSignal.timeout(5000),
        });
        if (res.ok) {
          setState((prev) => (prev === 'polling' ? 'polling' : 'connected'));
        } else {
          setState('disconnected');
        }
      } catch {
        setState('disconnected');
      }
    };

    connectWs();
    intervalRef.current = setInterval(checkPolling, 15000);

    return () => {
      wsRef.current?.close();
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const statusConfig: Record<ConnectionState, { label: string; color: string; dot: string }> = {
    connecting: {
      label: 'Connecting...',
      color: 'text-yellow-400',
      dot: 'bg-yellow-400 animate-pulse',
    },
    connected: {
      label: 'Live',
      color: 'text-emerald-400',
      dot: 'bg-emerald-400',
    },
    polling: {
      label: 'Polling',
      color: 'text-cyan-400',
      dot: 'bg-cyan-400',
    },
    disconnected: {
      label: 'Disconnected',
      color: 'text-red-400',
      dot: 'bg-red-400',
    },
  };

  const cfg = statusConfig[state];

  return (
    <div
      className="relative flex items-center gap-1.5"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className={cn('h-2 w-2 rounded-full', cfg.dot)} />
      <span className={cn('text-[11px] font-medium', cfg.color)}>
        {state === 'connected' ? 'Live' : state === 'polling' ? 'Poll' : ''}
      </span>

      {showTooltip && (
        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-dark-surface px-2 py-1 text-[11px] text-gray-300 shadow-lg border border-dark-border z-50">
          Real-time: {cfg.label}
        </div>
      )}
    </div>
  );
}
