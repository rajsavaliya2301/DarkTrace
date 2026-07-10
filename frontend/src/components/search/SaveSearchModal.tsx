import { useForm } from 'react-hook-form';
import { X } from 'lucide-react';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';

interface SaveSearchModalProps {
  query: string;
  onClose: () => void;
  onSaved: () => void;
}

interface SaveSearchFormData {
  name: string;
  notify_on_new: boolean;
}

export default function SaveSearchModal({ query, onClose, onSaved }: SaveSearchModalProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SaveSearchFormData>({
    defaultValues: {
      name: query.length > 60 ? query.slice(0, 60) + '...' : query,
      notify_on_new: false,
    },
  });

  const onSubmit = async (data: SaveSearchFormData) => {
    try {
      await apiClient.post('/search/saved', {
        name: data.name,
        query,
        filters: {},
        notify_on_new: data.notify_on_new,
      });
      toast.success('Search saved successfully');
      onSaved();
      onClose();
    } catch {
      toast.error('Failed to save search');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-xl border border-dark-border bg-dark-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-dark-border px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">Save Search</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-500 hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-6">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Name <span className="text-red-400">*</span>
            </label>
            <input
              {...register('name', { required: 'Name is required' })}
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="My saved search"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-400">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Query Preview
            </label>
            <p className="mt-1 text-xs text-gray-500 break-all line-clamp-2">
              {query}
            </p>
          </div>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              {...register('notify_on_new')}
              className="rounded border-dark-border bg-dark-card text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-300">
              Notify me when new results match this search
            </span>
          </label>

          <div className="flex justify-end gap-3 border-t border-dark-border pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-dark-border px-4 py-2 text-sm font-medium text-gray-300 hover:bg-dark-surface"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Search'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
