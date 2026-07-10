import { useState, useCallback, useEffect, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface SearchBarProps {
  placeholder?: string;
  className?: string;
  onSearch?: (query: string) => void;
  value?: string;
  autoFocus?: boolean;
}

export default function SearchBar({
  placeholder = 'Search alerts, actors, content...',
  className,
  onSearch,
  value: controlledValue,
  autoFocus = false,
}: SearchBarProps) {
  const navigate = useNavigate();

  // Initialize local state from the controlled value (URL query param).
  // We always display localValue so the user sees what they type immediately.
  const [localValue, setLocalValue] = useState(controlledValue ?? '');

  // When the URL param changes externally (e.g. page navigation, "clear all"),
  // sync it into local state so the input stays in sync.
  useEffect(() => {
    setLocalValue(controlledValue ?? '');
  }, [controlledValue]);

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      const trimmed = localValue.trim();
      if (!trimmed) return;
      if (onSearch) {
        onSearch(trimmed);
      } else {
        navigate(`/search?q=${encodeURIComponent(trimmed)}`);
      }
    },
    [localValue, navigate, onSearch]
  );

  const handleClear = useCallback(() => {
    setLocalValue('');
  }, []);

  return (
    <form onSubmit={handleSubmit} className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="w-full rounded-lg border border-dark-border bg-dark-surface py-2 pl-10 pr-10 text-sm text-gray-100 placeholder-gray-500 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        aria-label="Search"
      />
      {localValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </form>
  );
}
