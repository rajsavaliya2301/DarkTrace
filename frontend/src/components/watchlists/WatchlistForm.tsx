import { useForm, Controller } from 'react-hook-form';
import { X } from 'lucide-react';
import KeywordTagInput from './KeywordTagInput';
import type { CreateWatchlistRequest, Watchlist } from '../../types';

interface WatchlistFormProps {
  onSubmit: (data: CreateWatchlistRequest) => void;
  onCancel: () => void;
  initialData?: Watchlist;
  isLoading?: boolean;
}

export default function WatchlistForm({
  onSubmit,
  onCancel,
  initialData,
  isLoading,
}: WatchlistFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<CreateWatchlistRequest>({
    defaultValues: initialData
      ? {
          name: initialData.name,
          description: initialData.description,
          keywords: initialData.keywords,
          severity_boost: initialData.severity_boost,
          is_active: initialData.is_active,
        }
      : {
          name: '',
          description: '',
          keywords: [],
          severity_boost: 100,
          is_active: true,
        },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border border-dark-border bg-dark-card shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-dark-border px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">
            {initialData ? 'Edit Watchlist' : 'Create Watchlist'}
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
              Name
            </label>
            <input
              {...register('name', { required: 'Name is required' })}
              placeholder="Critical Infrastructure Keywords"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-400">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Description
            </label>
            <textarea
              {...register('description')}
              rows={2}
              placeholder="Keywords related to critical infrastructure targeting"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <Controller
            name="keywords"
            control={control}
            rules={{
              validate: (v) =>
                v.length > 0 || 'At least one keyword is required',
            }}
            render={({ field }) => (
              <div>
                <KeywordTagInput
                  keywords={field.value}
                  onChange={field.onChange}
                />
                {errors.keywords && (
                  <p className="mt-1 text-xs text-red-400">
                    {errors.keywords.message}
                  </p>
                )}
              </div>
            )}
          />

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Severity Boost
            </label>
            <input
              {...register('severity_boost', {
                valueAsNumber: true,
                min: { value: 0, message: 'Min 0' },
                max: { value: 500, message: 'Max 500' },
              })}
              type="number"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Extra score points for matched content (0-500)
            </p>
          </div>

          <div className="flex items-center gap-3">
            <label className="relative inline-flex cursor-pointer items-center">
              <input
                type="checkbox"
                {...register('is_active')}
                className="peer sr-only"
              />
              <div className="h-6 w-11 rounded-full bg-dark-border after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-gray-400 after:transition-all peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:bg-white" />
            </label>
            <span className="text-sm text-gray-300">Active</span>
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
              {isLoading
                ? 'Saving...'
                : initialData
                  ? 'Update Watchlist'
                  : 'Create Watchlist'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
