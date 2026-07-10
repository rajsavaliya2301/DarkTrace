import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, Trash2, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';
import { formatDateRelative } from '../../utils/formatters';
import type { SavedSearch } from '../../types';

interface SearchHistoryProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export default function SearchHistory({ isCollapsed, onToggle }: SearchHistoryProps) {
  const navigate = useNavigate();
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [loading, setLoading] = useState(true);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const fetchSavedSearches = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/search/saved');
      // API returns {data: [...], pagination: {...}}
      setSavedSearches(response.data.data ?? []);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSavedSearches();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/search/saved/${id}`);
      setSavedSearches((prev) => prev.filter((s) => s.id !== id));
      toast.success('Saved search deleted');
    } catch {
      toast.error('Failed to delete saved search');
    }
  };

  const handleGenerateReport = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setGeneratingId(id);
    try {
      await apiClient.post(`/search/saved/${id}/generate-report`);
      toast.success('Report generation started');
    } catch {
      toast.error('Failed to generate report');
    } finally {
      setGeneratingId(null);
    }
  };

  const handleNavigate = (saved: SavedSearch) => {
    navigate(`/search?q=${encodeURIComponent(saved.query)}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-gray-500" />
      </div>
    );
  }

  if (savedSearches.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <h3 className="text-sm font-semibold text-gray-200">
          Saved Searches ({savedSearches.length})
        </h3>
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        )}
      </button>

      {!isCollapsed && (
        <div className="border-t border-dark-border">
          {savedSearches.map((saved) => (
            <div
              key={saved.id}
              onClick={() => handleNavigate(saved)}
              className="flex cursor-pointer items-start gap-3 border-b border-dark-border px-4 py-3 transition-colors last:border-b-0 hover:bg-dark-surface"
            >
              <div className="mt-0.5 flex-shrink-0">
                <Search className="h-4 w-4 text-gray-500" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-200 truncate">
                  {saved.name}
                </p>
                <p className="mt-0.5 text-xs text-gray-500 truncate">
                  {saved.query}
                </p>
                <p className="mt-0.5 text-xs text-gray-600">
                  Saved {formatDateRelative(saved.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  onClick={(e) => handleGenerateReport(saved.id, e)}
                  disabled={generatingId === saved.id}
                  className="rounded p-1.5 text-gray-500 hover:text-blue-400 hover:bg-dark-border disabled:opacity-50"
                  title="Generate report"
                >
                  {generatingId === saved.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <FileText className="h-3.5 w-3.5" />
                  )}
                </button>
                <button
                  onClick={(e) => handleDelete(saved.id, e)}
                  className="rounded p-1.5 text-gray-500 hover:text-red-400 hover:bg-dark-border"
                  title="Delete saved search"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
