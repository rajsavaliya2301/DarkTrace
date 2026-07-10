import { useForm } from 'react-hook-form';
import { X } from 'lucide-react';
import { USER_ROLES, type UserRole } from '../../utils/constants';
import type { AdminUser } from '../../types';

interface UserFormValues {
  email: string;
  name: string;
  password: string;
  role: UserRole;
}

interface UserFormProps {
  onSubmit: (data: UserFormValues) => void;
  onCancel: () => void;
  initialData?: AdminUser;
  isLoading?: boolean;
}

export default function UserForm({
  onSubmit,
  onCancel,
  initialData,
  isLoading,
}: UserFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserFormValues>({
    defaultValues: initialData
      ? {
          email: initialData.email,
          name: initialData.name,
          password: '',
          role: initialData.role as UserRole,
        }
      : {
          email: '',
          name: '',
          password: '',
          role: 'investigator' as UserRole,
        },
  });

  const isEdit = !!initialData;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-xl border border-dark-border bg-dark-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-dark-border px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-100">
            {isEdit ? 'Edit User' : 'Add User'}
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
              placeholder="Inspector Sharma"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-400">
                {errors.name.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Email
            </label>
            <input
              type="email"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: 'Invalid email format',
                },
              })}
              placeholder="investigator@police.gov.in"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-400">
                {errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              {isEdit ? 'New Password (leave blank to keep)' : 'Password'}
            </label>
            <input
              type="password"
              {...register(
                'password',
                isEdit
                  ? {}
                  : { required: 'Password is required', minLength: { value: 8, message: 'Min 8 characters' } }
              )}
              placeholder="••••••••"
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-400">
                {errors.password.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">
              Role
            </label>
            <select
              {...register('role')}
              className="mt-1 w-full rounded-lg border border-dark-border bg-dark-surface px-3 py-2 text-sm text-gray-300 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {USER_ROLES.map((role) => (
                <option key={role} value={role}>
                  {role
                    .split('_')
                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                    .join(' ')}
                </option>
              ))}
            </select>
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
                : isEdit
                  ? 'Update User'
                  : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
