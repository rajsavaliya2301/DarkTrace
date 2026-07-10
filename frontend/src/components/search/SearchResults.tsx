import { useState, useCallback } from 'react';
import { Globe, User, Clock, ChevronLeft, ChevronRight, FileText, Shield, Link, Copy } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { SearchResult } from '../../types';
import { formatDateRelative } from '../../utils/formatters';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';

interface SearchResultsProps {
  results: SearchResult[] | undefined;
  isLoading: boolean;
  isError: boolean;
  total: number;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  query: string;
}

export default function SearchResults({
  results,
  isLoading,
  isError,
  total,
  page,
  totalPages,
  onPageChange,
  query,
}: SearchResultsProps) {
  const [showReportGenerator, setShowReportGenerator] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyUrl = useCallback(async (url: string, id: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedId(id);
      toast.success('URL copied to clipboard');
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error('Failed to copy URL');
    }
  }, []);

  const handleGenerateReport = async (data: { query: string; format: string; include_evidence: boolean }) => {
    try {
      await apiClient.post('/reports/from-search', data);
      toast.success('Report generation started');
      setShowReportGenerator(false);
    } catch {
      toast.error('Failed to generate report');
    }
  };

  if (!query) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-500">
        <EmptyState
          title="Search dark web content"
          message="Enter a search query to find content across crawled dark web sources. Supports Elasticsearch query syntax."
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <LoadingSpinner size="lg" label="Searching..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-8 text-center">
        <p className="text-red-400">Search failed. Please try again.</p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <EmptyState
        title="No results found"
        message={`No results found for "${query}". Try different keywords or fewer filters.`}
      />
    );
  }

  const highlightSnippet = (snippet: string) => {
    return snippet
      .replace(/<em>/g, '<mark class="bg-blue-500/30 text-blue-200 rounded px-0.5">')
      .replace(/<\/em>/g, '</mark>');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          Found <strong className="text-gray-300">{total.toLocaleString()}</strong> results
          for "{query}"
        </p>
        <button
          onClick={() => setShowReportGenerator(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          <FileText className="h-4 w-4" />
          Generate Report
        </button>
      </div>

      <div className="space-y-3">
        {results.map((result) => {
          const deepEntities = result.deep_entities;
          const totalDeepPII = deepEntities
            ? (deepEntities.indian_id_count || 0) + (deepEntities.phone_count || 0)
            : 0;

          return (
          <div
            key={result.id}
            className="rounded-xl border border-dark-border bg-dark-card p-4 transition-colors hover:border-gray-600"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Globe className="h-3 w-3" />
                  <span className="uppercase">{result.source_type}</span>
                  <span>·</span>
                  <span>{result.site_name}</span>
                  <span>·</span>
                  <User className="h-3 w-3" />
                  <span>{result.author}</span>
                  <span>·</span>
                  <Clock className="h-3 w-3" />
                  <span>{formatDateRelative(result.crawled_at)}</span>
                </div>
                <h3 className="mt-1 text-base font-semibold text-gray-100">
                  {result.title}
                </h3>
                <p
                  className="mt-1 text-sm text-gray-400 line-clamp-2"
                  dangerouslySetInnerHTML={{
                    __html: highlightSnippet(result.snippet),
                  }}
                />

                {/* Source URL — click to copy for Tor Browser */}
                {result.url && (
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    <Link className="h-3 w-3 shrink-0 text-gray-600" />
                    <span className="truncate font-mono text-gray-500">
                      {result.url}
                    </span>
                    {result.url.includes('.onion') && (
                      <span className="shrink-0 rounded bg-purple-500/15 px-1.5 py-0.5 text-[10px] font-medium text-purple-400">
                        TOR
                      </span>
                    )}
                    <button
                      onClick={() => handleCopyUrl(result.url, result.id)}
                      className="shrink-0 rounded p-1 text-gray-600 transition-colors hover:bg-dark-border hover:text-gray-300"
                      title="Copy URL — paste it in Tor Browser to view the live page"
                    >
                      {copiedId === result.id ? (
                        <span className="text-green-400 text-[10px] font-medium">Copied!</span>
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </button>
                  </div>
                )}

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className="rounded bg-dark-border px-2 py-0.5 text-xs text-gray-400 capitalize">
                    {result.category.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={cn(
                      'rounded px-2 py-0.5 text-xs font-medium',
                      result.severity_score >= 700
                        ? 'bg-red-500/20 text-red-400'
                        : result.severity_score >= 400
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-gray-500/20 text-gray-400'
                    )}
                  >
                    Score: {result.severity_score}
                  </span>
                  {result.matched_entities?.btc_addresses && (
                    <span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs text-amber-400">
                      BTC
                    </span>
                  )}
                  {result.matched_entities?.emails && (
                    <span className="rounded bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400">
                      Email
                    </span>
                  )}

                  {/* Indian PII Badges */}
                  {result.matched_entities?.indian_ids?.some(item => item.type === 'aadhaar') && (
                    <span className="rounded bg-orange-500/10 px-2 py-0.5 text-xs text-orange-400">
                      Aadhaar
                    </span>
                  )}
                  {result.matched_entities?.indian_ids?.some(item => item.type === 'pan') && (
                    <span className="rounded bg-purple-500/10 px-2 py-0.5 text-xs text-purple-400">
                      PAN
                    </span>
                  )}
                  {result.matched_entities?.indian_ids?.some(item => item.type === 'voter_id') && (
                    <span className="rounded bg-pink-500/10 px-2 py-0.5 text-xs text-pink-400">
                      Voter ID
                    </span>
                  )}
                  {result.matched_entities?.indian_ids?.some(item => item.type === 'passport') && (
                    <span className="rounded bg-yellow-500/10 px-2 py-0.5 text-xs text-yellow-400">
                      Indian Passport
                    </span>
                  )}
                  {result.matched_entities?.phone_numbers && result.matched_entities.phone_numbers.length > 0 && (
                    <span className="rounded bg-teal-500/10 px-2 py-0.5 text-xs text-teal-400">
                      Indian Phone
                    </span>
                  )}

                  {/* Deep Scan Badge */}
                  {totalDeepPII > 0 && (
                    <span className="inline-flex items-center gap-1 rounded bg-cyan-500/15 px-2 py-0.5 text-xs font-medium text-cyan-400">
                      <Shield className="h-3 w-3" />
                      Deep Scan ({totalDeepPII})
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
          );
        })}
      </div>

      {showReportGenerator && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-xl border border-dark-border bg-dark-card shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-dark-border px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-100">
                Generate Report from Search
              </h2>
              <button
                onClick={() => setShowReportGenerator(false)}
                className="rounded p-1 text-gray-500 hover:text-gray-300"
              >
                <span className="text-lg">&times;</span>
              </button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const form = e.currentTarget;
                const formData = new FormData(form);
                handleGenerateReport({
                  query,
                  format: (formData.get('format') as string) || 'json',
                  include_evidence: formData.get('include_evidence') === 'on',
                });
              }}
              className="space-y-4 p-6"
            >
              <div>
                <label className="block text-sm font-medium text-gray-300">Format</label>
                <select
                  name="format"
                  defaultValue="json"
                  className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="json">JSON</option>
                  <option value="csv">CSV</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  name="include_evidence"
                  defaultChecked
                  className="rounded border-dark-border bg-dark-card text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-300">Include evidence</span>
              </label>
              <div className="flex justify-end gap-3 border-t border-dark-border pt-4">
                <button
                  type="button"
                  onClick={() => setShowReportGenerator(false)}
                  className="rounded-md border border-dark-border px-4 py-2 text-sm font-medium text-gray-300 hover:bg-dark-surface"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Generate Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="rounded p-1 text-gray-400 hover:text-gray-200 disabled:opacity-50"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="rounded p-1 text-gray-400 hover:text-gray-200 disabled:opacity-50"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
