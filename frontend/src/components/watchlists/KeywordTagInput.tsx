import { useState, type KeyboardEvent } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface KeywordTagInputProps {
  keywords: string[];
  onChange: (keywords: string[]) => void;
  placeholder?: string;
  label?: string;
}

export default function KeywordTagInput({
  keywords,
  onChange,
  placeholder = 'Type a keyword and press Enter',
  label = 'Keywords',
}: KeywordTagInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addKeyword = () => {
    const trimmed = inputValue.trim().toLowerCase();
    if (trimmed && !keywords.includes(trimmed)) {
      onChange([...keywords, trimmed]);
    }
    setInputValue('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addKeyword();
    }
  };

  const removeKeyword = (keyword: string) => {
    onChange(keywords.filter((k) => k !== keyword));
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        {label}
      </label>
      <div
        className={cn(
          'flex flex-wrap items-center gap-1.5 rounded-lg border border-dark-border bg-dark-surface p-2 min-h-[42px]',
          'focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500'
        )}
      >
        {keywords.map((kw) => (
          <span
            key={kw}
            className="inline-flex items-center gap-1 rounded bg-blue-500/15 px-2 py-0.5 text-xs font-medium text-blue-400"
          >
            {kw}
            <button
              onClick={() => removeKeyword(kw)}
              className="hover:text-blue-200"
              aria-label={`Remove keyword ${kw}`}
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={addKeyword}
          placeholder={keywords.length === 0 ? placeholder : ''}
          className="min-w-[100px] flex-1 bg-transparent text-sm text-gray-100 placeholder-gray-500 outline-none"
          aria-label="Add keyword"
        />
      </div>
      <p className="mt-1 text-xs text-gray-500">
        Press Enter or tab to add a keyword
      </p>
    </div>
  );
}
