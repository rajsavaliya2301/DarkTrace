import { X } from 'lucide-react';
import { cn } from '../../utils/cn';
import { SOURCE_TYPES, ALERT_CATEGORIES } from '../../utils/constants';
import type { SearchFacets } from '../../types';

interface SearchFiltersProps {
  facets: SearchFacets | undefined;
  selectedCategory: string;
  selectedSourceType: string;
  selectedLanguage: string;
  onCategoryChange: (value: string) => void;
  onSourceTypeChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  hasActiveFilters: boolean;
  onClearFilters: () => void;
}

export default function SearchFilters({
  facets,
  selectedCategory,
  selectedSourceType,
  selectedLanguage,
  onCategoryChange,
  onSourceTypeChange,
  onLanguageChange,
  hasActiveFilters,
  onClearFilters,
}: SearchFiltersProps) {
  const filterSection = (
    label: string,
    items: { value: string; count: number }[] | undefined,
    selectedValue: string,
    onChange: (value: string) => void,
    formatLabel?: (v: string) => string
  ) => (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
        {label}
      </h4>
      <div className="space-y-0.5">
        <button
          onClick={() => onChange('')}
          className={cn(
            'flex w-full items-center justify-between rounded px-2 py-1 text-left text-xs',
            !selectedValue
              ? 'bg-blue-500/10 text-blue-400'
              : 'text-gray-400 hover:bg-dark-card'
          )}
        >
          <span>All</span>
        </button>
        {items?.map((item) => (
          <button
            key={item.value}
            onClick={() => onChange(item.value)}
            className={cn(
              'flex w-full items-center justify-between rounded px-2 py-1 text-left text-xs',
              selectedValue === item.value
                ? 'bg-blue-500/10 text-blue-400'
                : 'text-gray-400 hover:bg-dark-card'
            )}
          >
            <span>
              {formatLabel ? formatLabel(item.value) : item.value}
            </span>
            <span className="text-gray-600">{item.count}</span>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {hasActiveFilters && (
        <button
          onClick={onClearFilters}
          className="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200"
        >
          <X className="h-3 w-3" />
          Clear all filters
        </button>
      )}

      {filterSection(
        'Category',
        facets?.categories,
        selectedCategory,
        onCategoryChange,
        (v) => v.replace(/_/g, ' ')
      )}
      {filterSection(
        'Source Type',
        facets?.source_types,
        selectedSourceType,
        onSourceTypeChange,
        (v) =>
          v === 'onion' ? 'Tor (.onion)' : v === 'i2p' ? 'I2P' : 'Surface'
      )}
      {filterSection(
        'Language',
        facets?.languages,
        selectedLanguage,
        onLanguageChange,
        (v) => v.toUpperCase()
      )}
    </div>
  );
}
