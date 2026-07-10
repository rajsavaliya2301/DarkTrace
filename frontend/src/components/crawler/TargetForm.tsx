import { useForm } from 'react-hook-form';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';
import {
  CRAWL_FREQUENCIES,
  PARSER_TYPES,
  SOURCE_TYPES,
  type SourceType,
  type CrawlFrequency,
  type ParserType,
} from '../../utils/constants';
import type { AddTargetRequest } from '../../types';

interface TargetFormProps {
  onSubmit: (data: AddTargetRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function TargetForm({
  onSubmit,
  onCancel,
  isLoading,
}: TargetFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AddTargetRequest>({
    defaultValues: {
      url: '',
      site_name: '',
      source_type: 'onion' as SourceType,
      crawl_frequency: 'every_6h' as CrawlFrequency,
      parser_type: 'marketplace' as ParserType,
      notes: '',
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border border-dark-border bg-dark-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-dark-border px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">
            Add Crawl Target
          </h2>
          <button
            onClick={onCancel}
            className="rounded p-1 text-gray-500 hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-6">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              URL
            </label>
            <input
              {...register('url', { required: 'URL is required' })}
              placeholder="http://example.onion"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.url && (
              <p className="mt-1 text-xs text-red-400">{errors.url.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Site Name
            </label>
            <input
              {...register('site_name', { required: 'Site name is required' })}
              placeholder="ExampleMarket"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.site_name && (
              <p className="mt-1 text-xs text-red-400">
                {errors.site_name.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Source Type
              </label>
              <select
                {...register('source_type')}
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {SOURCE_TYPES.map((st) => (
                  <option key={st} value={st}>
                    {st === 'onion' ? 'Tor (.onion)' : st === 'i2p' ? 'I2P' : 'Surface Web'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">
                Crawl Frequency
              </label>
              <select
                {...register('crawl_frequency')}
                className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {CRAWL_FREQUENCIES.map((freq) => (
                  <option key={freq} value={freq}>
                    {freq
                      .replace('every_', 'Every ')
                      .replace('_', ' ')
                      .replace('weekly', 'Weekly')}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Parser Type
            </label>
            <select
              {...register('parser_type')}
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {PARSER_TYPES.map((pt) => (
                <option key={pt} value={pt}>
                  {pt.charAt(0).toUpperCase() + pt.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Notes (optional)
            </label>
            <textarea
              {...register('notes')}
              rows={3}
              placeholder="Any additional information..."
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-3 border-t border-dark-border pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-md border border-dark-border px-4 py-2 text-sm font-medium text-gray-300 hover:bg-dark-surface"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Adding...' : 'Add Target'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
