import {
  ArrowLeft,
  ExternalLink,
  User,
  Clock,
  Activity,
  AlertTriangle,
  Hash,
  Mail,
  Bitcoin,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import StatusBadge from '../common/StatusBadge';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorState from '../common/ErrorState';
import { formatDate, formatDateRelative } from '../../utils/formatters';
import type { AlertDetail as AlertDetailType } from '../../types';
import type { SeverityLevel } from '../../utils/constants';

interface AlertDetailProps {
  data: AlertDetailType | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
}

export default function AlertDetailView({
  data,
  isLoading,
  isError,
  onRetry,
}: AlertDetailProps) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Loading alert details..." />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Failed to load alert"
        message="Could not load alert details. Please try again."
        onRetry={onRetry}
      />
    );
  }

  const scoreEntries = data.score_breakdown
    ? Object.entries(data.score_breakdown)
    : [];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/alerts')}
        className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Alerts
      </button>

      {/* Header */}
      <div className="rounded-xl border border-dark-border bg-dark-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <StatusBadge severity={data.severity as SeverityLevel} size="md" />
              <span className="rounded bg-dark-border px-2 py-0.5 text-xs text-gray-400 uppercase">
                {data.category.replace(/_/g, ' ')}
              </span>
              <span className="text-xs text-gray-500">
                Score: <strong className="text-gray-300">{data.score}</strong>
              </span>
            </div>
            <h1 className="mt-3 text-xl font-bold text-gray-100">
              {data.title}
            </h1>
            <p className="mt-2 text-sm text-gray-400">{data.content?.content_text}</p>
          </div>
        </div>

        {/* Status actions */}
        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-dark-border pt-4">
          <span className="text-sm text-gray-500">
            Status:{' '}
            <span className="font-medium text-gray-300 capitalize">
              {data.status.replace(/_/g, ' ')}
            </span>
          </span>
          <span className="text-sm text-gray-500">
            Assignee:{' '}
            <span className="font-medium text-gray-300">
              {data.assignee || 'Unassigned'}
            </span>
          </span>
        </div>
      </div>

      {/* Source & Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">
            Source Information
          </h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <ExternalLink className="mt-0.5 h-4 w-4 shrink-0 text-gray-500" />
              <div className="min-w-0">
                <p className="text-xs text-gray-500">URL</p>
                <p className="break-all text-sm font-mono text-blue-400">
                  {data.source?.url}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Hash className="h-4 w-4 shrink-0 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Site</p>
                <p className="text-sm text-gray-300">
                  {data.source?.site_name}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 shrink-0 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Crawled At</p>
                <p className="text-sm text-gray-300">
                  {formatDate(data.source?.crawl_timestamp)}
                </p>
              </div>
            </div>
          </div>

          <h3 className="mb-3 mt-6 text-sm font-semibold text-gray-200">
            Content
          </h3>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-gray-500">Title</p>
              <p className="text-sm text-gray-300">{data.content?.title}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Author</p>
              <p className="text-sm text-purple-400">
                {data.content?.author || 'Unknown'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Published</p>
              <p className="text-sm text-gray-300">
                {data.content?.published_date || 'Unknown'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Language</p>
              <p className="text-sm text-gray-300 uppercase">
                {data.content?.language}
                {data.content?.translated_from && (
                  <span className="text-gray-500">
                    {' '}
                    (translated from {data.content.translated_from})
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Entities & Analysis */}
        <div className="space-y-6">
          <div className="rounded-xl border border-dark-border bg-dark-card p-5">
            <h3 className="mb-4 text-sm font-semibold text-gray-200">
              Entities Detected
            </h3>
            <div className="space-y-4">
              {data.entities?.keywords_matched &&
                data.entities.keywords_matched.length > 0 && (
                  <div>
                    <p className="mb-2 flex items-center gap-1 text-xs text-gray-500">
                      <AlertTriangle className="h-3 w-3" />
                      Matched Keywords
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {data.entities.keywords_matched.map((kw) => (
                        <span
                          key={kw}
                          className="rounded bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              {data.entities?.btc_addresses &&
                data.entities.btc_addresses.length > 0 && (
                  <div>
                    <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                      <Bitcoin className="h-3 w-3" />
                      BTC Addresses
                    </p>
                    {data.entities.btc_addresses.map((addr) => (
                      <p
                        key={addr}
                        className="font-mono text-xs text-amber-400"
                      >
                        {addr}
                      </p>
                    ))}
                  </div>
                )}
              {data.entities?.emails && data.entities.emails.length > 0 && (
                <div>
                  <p className="mb-1 flex items-center gap-1 text-xs text-gray-500">
                    <Mail className="h-3 w-3" />
                    Emails
                  </p>
                  {data.entities.emails.map((email) => (
                    <p key={email} className="font-mono text-xs text-blue-400">
                      {email}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-dark-border bg-dark-card p-5">
            <h3 className="mb-4 text-sm font-semibold text-gray-200">
              Analysis
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-gray-500">Threat Intent</p>
                <p className="text-lg font-bold text-red-400">
                  {(data.analysis?.sentiment?.threat_intent * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Hostility</p>
                <p className="text-lg font-bold text-amber-400">
                  {(data.analysis?.sentiment?.hostility * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Urgency</p>
                <p className="text-lg font-bold text-cyan-400">
                  {(data.analysis?.sentiment?.urgency * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            {data.analysis?.classification && (
              <div className="mt-4">
                <p className="text-xs text-gray-500">Classification</p>
                <p className="text-sm font-medium text-gray-300 capitalize">
                  {data.analysis.classification.primary}
                </p>
                <p className="text-xs text-gray-500">
                  Confidence: {(data.analysis.classification.confidence * 100).toFixed(0)}%
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Score Breakdown */}
      {scoreEntries.length > 0 && (
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">
            Score Breakdown
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {scoreEntries.map(([key, val]) => (
              <div
                key={key}
                className="rounded-lg bg-dark-surface p-3"
              >
                <p className="text-xs text-gray-500 capitalize">
                  {key.replace(/_/g, ' ')}
                </p>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-lg font-bold text-gray-200">
                    {val.score}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({(val.weight * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actor Info */}
      {data.actor && (
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-200">
            <User className="h-4 w-4" />
            Actor Profile
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs text-gray-500">Pseudonyms</p>
              <p className="text-sm text-purple-400">
                {data.actor.pseudonyms.join(', ')}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Risk Score</p>
              <p className="text-lg font-bold text-red-400">
                {data.actor.risk_score}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">First Seen</p>
              <p className="text-sm text-gray-300">
                {formatDate(data.actor.first_seen)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Last Seen</p>
              <p className="text-sm text-gray-300">
                {formatDate(data.actor.last_seen)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline */}
      {data.timeline && data.timeline.length > 0 && (
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-200">
            <Activity className="h-4 w-4" />
            Alert Timeline
          </h3>
          <div className="relative space-y-0">
            {data.timeline.map((event, index) => (
              <div key={index} className="relative flex gap-4 pb-4">
                {index < data.timeline.length - 1 && (
                  <div className="absolute left-2 top-4 bottom-0 w-px bg-dark-border" />
                )}
                <div className="relative z-10 flex h-4 w-4 shrink-0 items-center justify-center">
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-200 capitalize">
                    {event.event}
                  </p>
                  <p className="text-xs text-gray-500">{event.detail}</p>
                  <p className="text-xs text-gray-600">
                    {formatDateRelative(event.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related Alerts */}
      {data.related_alerts && data.related_alerts.length > 0 && (
        <div className="rounded-xl border border-dark-border bg-dark-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">
            Related Alerts
          </h3>
          <div className="space-y-2">
            {data.related_alerts.map((related) => (
              <button
                key={related.id}
                onClick={() => navigate(`/alerts/${related.id}`)}
                className="flex w-full items-center justify-between rounded-lg bg-dark-surface p-3 text-left hover:bg-dark-border"
              >
                <span className="text-sm text-gray-300">{related.title}</span>
                <div className="flex items-center gap-2">
                  <StatusBadge severity={related.severity as SeverityLevel} />
                  <span className="text-xs text-gray-500">
                    {formatDateRelative(related.created_at)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
