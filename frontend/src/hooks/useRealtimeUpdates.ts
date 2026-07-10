import { useEffect, useRef, useCallback } from 'react';
import { WS_BASE_URL, API_BASE_URL } from '../utils/constants';

type EventHandler = (event: Record<string, unknown>) => void;

interface UseRealtimeUpdatesOptions {
  channels?: string;
  onAlert?: EventHandler;
  onContent?: EventHandler;
  onActor?: EventHandler;
  onDashboard?: EventHandler;
  enabled?: boolean;
}

/**
 * Hook for real-time updates via WebSocket.
 * Falls back to polling if WebSocket fails.
 *
 * Usage:
 * ```ts
 * useRealtimeUpdates({
 *   channels: 'alert,dashboard',
 *   onAlert: (event) => console.log('New alert:', event),
 *   onDashboard: (event) => refetch(),
 * });
 * ```
 */
export function useRealtimeUpdates(options: UseRealtimeUpdatesOptions) {
  const {
    channels = 'alert,dashboard',
    onAlert,
    onContent,
    onActor,
    onDashboard,
    enabled = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastEventTimeRef = useRef<number>(Date.now());

  const connectWebSocket = useCallback(() => {
    if (!enabled) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const base = WS_BASE_URL.replace('/v1', '').replace(/\/+$/, '');
    const url = `${base}/ws/events?channels=${channels}`;
    console.log('[Realtime] Connecting WebSocket:', url);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[Realtime] WebSocket connected');
        // Clear polling if active
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Skip heartbeats
          if (data.type === 'heartbeat' || data.type === 'connected') return;

          lastEventTimeRef.current = Date.now();

          // Route to appropriate handler
          switch (data.type) {
            case 'alert_created':
              onAlert?.(data);
              break;
            case 'content_processed':
              onContent?.(data);
              break;
            case 'actor_updated':
              onActor?.(data);
              break;
            case 'dashboard_update':
              onDashboard?.(data);
              break;
            default:
              // Try routing by channel
              if (data.channel === 'alert') onAlert?.(data);
              else if (data.channel === 'content') onContent?.(data);
              else if (data.channel === 'actor') onActor?.(data);
              else if (data.channel === 'dashboard') onDashboard?.(data);
          }
        } catch (e) {
          console.warn('[Realtime] Failed to parse message:', e);
        }
      };

      ws.onclose = () => {
        console.log('[Realtime] WebSocket disconnected, will reconnect in 5s');
        wsRef.current = null;
        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
        // Fall back to polling
        startPolling();
      };

      ws.onerror = (err) => {
        console.warn('[Realtime] WebSocket error, falling back to polling:', err);
        ws.close();
        startPolling();
      };
    } catch (err) {
      console.warn('[Realtime] Failed to create WebSocket, using polling:', err);
      startPolling();
    }
  }, [channels, enabled, onAlert, onContent, onActor, onDashboard]);

  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return;

    console.log('[Realtime] Starting polling fallback');
    pollIntervalRef.current = setInterval(async () => {
      try {
        const baseUrl = (window as any).__API_BASE_URL__ || '/v1';
        const responses = await Promise.allSettled(
          ['alert', 'content', 'actor', 'dashboard']
            .filter((ch) => channels.includes(ch))
            .map(async (ch) => {
              const res = await fetch(
                `${baseUrl}/events/poll?channel=${ch}&since=${lastEventTimeRef.current / 1000}&limit=5`
              );
              if (!res.ok) return;
              const data = await res.json();
              for (const event of data.events || []) {
                switch (event.type) {
                  case 'alert_created':
                    onAlert?.(event);
                    break;
                  case 'content_processed':
                    onContent?.(event);
                    break;
                  case 'actor_updated':
                    onActor?.(event);
                    break;
                  case 'dashboard_update':
                    onDashboard?.(event);
                    break;
                }
              }
            })
        );
      } catch (err) {
        // Silent fail for polling
      }
    }, 3000);
  }, [channels, onAlert, onContent, onActor, onDashboard]);

  useEffect(() => {
    if (!enabled) return;

    // Try WebSocket first
    connectWebSocket();

    return () => {
      // Cleanup
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [enabled, connectWebSocket]);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    isPolling: pollIntervalRef.current !== null,
  };
}
