import {
  ArrowLeft,
  User,
  Activity,
  AlertTriangle,
  Bitcoin,
  Mail,
  Key,
  Calendar,
  Globe,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorState from '../common/ErrorState';
import { formatDate, formatDateRelative } from '../../utils/formatters';
import type { ActorDetail as ActorDetailType } from '../../types';
import ActorNetworkGraph from './ActorNetworkGraph';

interface ActorDetailProps {
  data: ActorDetailType | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
}

export default function ActorDetailView({
  data,
  isLoading,
  isError,
  onRetry,
}: ActorDetailProps) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Loading actor profile..." />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Failed to load actor"
        message="Could not load actor profile. Please try again."
        onRetry={onRetry}
      />
    );
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/actors')}
        className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Actors
      </button>

      {/* Header */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-500/20">
              <User className="h-7 w-7 text-red-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-100">
                {data.pseudonyms[0]?.name || 'Unknown'}
              </h1>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-gray-400">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  First seen: {formatDate(data.first_seen)}
                </span>
                <span className="flex items-center gap-1">
                  <Activity className="h-3.5 w-3.5" />
                  Last seen: {formatDateRelative(data.last_seen)}
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">Risk Score</p>
            <p className="text-3xl font-bold text-red-400">
              {data.risk_score}
            </p>
          </div>
        </div>

        {/* Risk Factors */}
        {data.risk_factors && data.risk_factors.length > 0 && (
          <div className="mt-6 border-t border-dark-border pt-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Risk Factors
            </p>
            <div className="flex flex-wrap gap-2">
              {data.risk_factors.map((rf, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded bg-red-500/10 px-2 py-1 text-xs text-red-400"
                >
                  <AlertTriangle className="h-3 w-3" />
                  {rf}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Pseudonyms */}
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-200">
            <User className="h-4 w-4" />
            Aliases
          </h3>
          <div className="space-y-3">
            {data.pseudonyms.map((p) => (
              <div
                key={p.name}
                className="rounded-lg bg-dark-surface p-3"
              >
                <p className="text-sm font-medium text-purple-400">
                  {p.name}
                </p>
                <p className="text-xs text-gray-500">
                  {p.platforms.join(', ')}
                </p>
                <p className="text-xs text-gray-600">
                  {formatDate(p.first_seen)} — {formatDate(p.last_seen)}
                </p>
              </div>
            ))}
          </div>

          <h3 className="mb-3 mt-6 flex items-center gap-2 text-sm font-semibold text-gray-200">
            <Globe className="h-4 w-4" />
            Active Platforms
          </h3>
          <div className="flex flex-wrap gap-2">
            {data.active_platforms.map((p) => (
              <span
                key={p}
                className="rounded bg-dark-border px-2 py-1 text-xs text-gray-300"
              >
                {p}
              </span>
            ))}
          </div>
        </div>

        {/* Linked Entities */}
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">
            Linked Entities
          </h3>
          <div className="space-y-4">
            {data.linked_entities?.btc_addresses &&
              data.linked_entities.btc_addresses.length > 0 && (
                <div>
                  <p className="mb-2 flex items-center gap-1 text-xs text-gray-500">
                    <Bitcoin className="h-3 w-3" />
                    BTC Addresses
                  </p>
                  {data.linked_entities.btc_addresses.map((btc) => (
                    <div
                      key={btc.address}
                      className="mb-1 rounded bg-dark-surface p-2"
                    >
                      <p className="font-mono text-xs text-amber-400 break-all">
                        {btc.address}
                      </p>
                      <p className="text-xs text-gray-500">
                        {btc.total_received_btc} BTC received
                      </p>
                    </div>
                  ))}
                </div>
              )}
            {data.linked_entities?.emails &&
              data.linked_entities.emails.length > 0 && (
                <div>
                  <p className="mb-2 flex items-center gap-1 text-xs text-gray-500">
                    <Mail className="h-3 w-3" />
                    Emails
                  </p>
                  {data.linked_entities.emails.map((email) => (
                    <p
                      key={email}
                      className="font-mono text-xs text-blue-400 mb-1"
                    >
                      {email}
                    </p>
                  ))}
                </div>
              )}
            {data.linked_entities?.pgp_keys &&
              data.linked_entities.pgp_keys.length > 0 && (
                <div>
                  <p className="mb-2 flex items-center gap-1 text-xs text-gray-500">
                    <Key className="h-3 w-3" />
                    PGP Keys
                  </p>
                  {data.linked_entities.pgp_keys.map((pgp) => (
                    <p key={pgp} className="font-mono text-xs text-green-400">
                      {pgp}
                    </p>
                  ))}
                </div>
              )}
          </div>
        </div>

        {/* Activity Timeline */}
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-200">
            <Activity className="h-4 w-4" />
            Activity Timeline
          </h3>
          <div className="relative space-y-0">
            {data.activity_timeline?.slice(-6).map((act, idx) => (
              <div key={act.date} className="relative flex gap-3 pb-4">
                {idx < Math.min(data.activity_timeline.length, 6) - 1 && (
                  <div className="absolute left-2 top-4 bottom-0 w-px bg-dark-border" />
                )}
                <div className="relative z-10 mt-1 h-3 w-3 shrink-0 rounded-full bg-blue-500" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-200">
                    {act.date}
                  </p>
                  <p className="text-xs text-gray-400">
                    {act.posts} posts
                  </p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {act.categories.map((cat) => (
                      <span
                        key={cat}
                        className="rounded bg-dark-border px-1.5 py-0.5 text-xs text-gray-400"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Network Graph */}
      {data.network_graph && (
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">
            Network Graph
          </h3>
          <div className="h-[400px]">
            <ActorNetworkGraph graph={data.network_graph} />
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {data.recent_activity && data.recent_activity.length > 0 && (
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">
            Recent Activity
          </h3>
          <div className="space-y-2">
            {data.recent_activity.map((item) => (
              <div
                key={item.content_id}
                className="rounded-lg bg-dark-surface p-3"
              >
                <p className="text-sm font-medium text-gray-200">
                  {item.title}
                </p>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                  <span className="capitalize">{item.category}</span>
                  <span>{formatDateRelative(item.crawled_at)}</span>
                  <span className="font-mono text-blue-400 truncate max-w-[200px]">
                    {item.url}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
