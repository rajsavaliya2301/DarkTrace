import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Save, Shield } from 'lucide-react';
import { cn } from '../utils/cn';
import PageHeader from '../components/common/PageHeader';
import SearchBar from '../components/common/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import SearchResults from '../components/search/SearchResults';
import SaveSearchModal from '../components/search/SaveSearchModal';
import SearchHistory from '../components/search/SearchHistory';
import { useSearch } from '../hooks/useSearch';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';
import { toast } from 'react-hot-toast';
import type { SearchResponse } from '../types';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);

  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSourceType, setSelectedSourceType] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [deepScan, setDeepScan] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showSavedSearches, setShowSavedSearches] = useState(true);

  const searchParams_obj = {
    q: query,
    page,
    per_page: 25,
    category: selectedCategory || undefined,
    source_type: (selectedSourceType || undefined) as any,
    language: selectedLanguage || undefined,
    sort_by: 'relevance' as const,
    deep_search: deepScan || undefined,
  };

  const { data, isLoading, isError, refetch } = useSearch(searchParams_obj);

  // Real-time content updates
  useRealtimeUpdates({
    channels: 'content',
    onContent: (event) => {
      const action = event.action as string;
      if (action === 'new_content' && query) {
        toast(`📄 New content indexed: ${(event.title as string)?.slice(0, 50) || 'Untitled'}`, {
          duration: 3000,
          style: { background: '#1f2937', color: '#f9fafb' },
        });
      }
    },
  });

  // API returns {data: SearchResult[], pagination, facets} directly
  // Axios strips the outer layer, so `data` = the full response object
  const results = data?.data ?? [];
  const total = data?.pagination?.total ?? 0;
  const totalPages = data?.pagination?.total_pages ?? 0;
  const facets = data?.facets;

  const handleSearch = useCallback(
    (q: string) => {
      setSearchParams({ q });
      setSelectedCategory('');
      setSelectedSourceType('');
      setSelectedLanguage('');
      setDeepScan(false);
    },
    [setSearchParams, setDeepScan]
  );

  const handlePageChange = (newPage: number) => {
    setSearchParams({ q: query, page: String(newPage) });
  };

  const hasActiveFilters = !!(selectedCategory || selectedSourceType || selectedLanguage);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Search"
        subtitle="Search across all crawled dark web content"
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <SearchBar
          onSearch={handleSearch}
          value={query}
          autoFocus
          placeholder="Use Elasticsearch syntax: ransomware OR lockbit, author:dark_hand, category:ransomware"
          className="max-w-2xl flex-1"
        />

        {query && (
          <div className="flex items-center gap-2">
            {/* Deep Scan Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={deepScan}
                  onChange={(e) => setDeepScan(e.target.checked)}
                  className="sr-only peer"
                />
                <div className={cn(
                  'w-10 h-5 rounded-full transition-colors',
                  deepScan ? 'bg-cyan-600' : 'bg-dark-border'
                )}>
                  <div className={cn(
                    'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform',
                    deepScan && 'translate-x-5'
                  )} />
                </div>
              </div>
              <span className={cn(
                'text-xs font-medium flex items-center gap-1',
                deepScan ? 'text-cyan-400' : 'text-gray-400'
              )}>
                <Shield className="h-3.5 w-3.5" />
                Deep Scan
              </span>
            </label>

            <button
              onClick={() => setShowSaveModal(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-dark-border px-3 py-2 text-sm font-medium text-gray-300 hover:bg-dark-surface"
            >
              <Save className="h-4 w-4" />
              Save Search
            </button>
          </div>
        )}
      </div>

      {/* Saved Searches Section (collapsible, visible when no active search or as sidebar) */}
      {!query && (
        <SearchHistory
          isCollapsed={!showSavedSearches}
          onToggle={() => setShowSavedSearches(!showSavedSearches)}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-4">
        {query && (
          <div className="lg:col-span-1">
            <div className="rounded-xl border border-dark-border bg-dark-card p-4">
              <h3 className="mb-4 text-sm font-semibold text-gray-200">
                Filters
              </h3>
              <SearchFilters
                facets={facets}
                selectedCategory={selectedCategory}
                selectedSourceType={selectedSourceType}
                selectedLanguage={selectedLanguage}
                onCategoryChange={setSelectedCategory}
                onSourceTypeChange={setSelectedSourceType}
                onLanguageChange={setSelectedLanguage}
                hasActiveFilters={hasActiveFilters}
                onClearFilters={() => {
                  setSelectedCategory('');
                  setSelectedSourceType('');
                  setSelectedLanguage('');
                }}
              />
            </div>

            {/* Saved Searches Sidebar */}
            <div className="mt-4">
              <SearchHistory
                isCollapsed={!showSavedSearches}
                onToggle={() => setShowSavedSearches(!showSavedSearches)}
              />
            </div>
          </div>
        )}

        <div className={query ? 'lg:col-span-3' : 'lg:col-span-4'}>
          <SearchResults
            results={results}
            isLoading={isLoading}
            isError={isError}
            total={total}
            page={page}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            query={query}
          />
        </div>
      </div>

      {showSaveModal && (
        <SaveSearchModal
          query={query}
          onClose={() => setShowSaveModal(false)}
          onSaved={() => refetch()}
        />
      )}
    </div>
  );
}
