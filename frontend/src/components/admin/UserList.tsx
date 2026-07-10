import DataTable, { type Column } from '../common/DataTable';
import { formatDate, formatDateRelative } from '../../utils/formatters';
import type { AdminUser } from '../../types';
import { cn } from '../../utils/cn';

interface UserListProps {
  users: AdminUser[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry?: () => void;
  onEdit?: (user: AdminUser) => void;
}

export default function UserList({
  users,
  isLoading,
  isError,
  onRetry,
  onEdit,
}: UserListProps) {
  const columns: Column<AdminUser>[] = [
    {
      key: 'name',
      header: 'Name',
      render: (user) => (
        <div>
          <p className="text-sm font-medium text-gray-200">{user.name}</p>
          <p className="text-xs text-gray-500">{user.email}</p>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      width: '120px',
      render: (user) => (
        <span
          className={cn(
            'inline-block rounded-full px-2 py-0.5 text-xs font-medium',
            user.role === 'admin'
              ? 'bg-purple-500/20 text-purple-400'
              : user.role === 'investigator'
                ? 'bg-blue-500/20 text-blue-400'
                : user.role === 'auditor'
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-gray-500/20 text-gray-400'
          )}
        >
          {user.role.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      width: '80px',
      render: (user) => (
        <span
          className={cn(
            'inline-block rounded-full px-2 py-0.5 text-xs font-medium',
            user.is_active
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-red-500/20 text-red-400'
          )}
        >
          {user.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'last_login',
      header: 'Last Login',
      width: '140px',
      hideOnMobile: true,
      render: (user) => (
        <span className="text-xs text-gray-400">
          {user.last_login ? formatDateRelative(user.last_login) : 'Never'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      width: '100px',
      hideOnMobile: true,
      render: (user) => (
        <span className="text-xs text-gray-400">
          {formatDate(user.created_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '50px',
      render: (user) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onEdit?.(user);
          }}
          className="rounded p-1 text-gray-500 hover:text-gray-300"
        >
          Edit
        </button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={users || []}
      keyExtractor={(u) => u.id}
      isLoading={isLoading}
      isError={isError}
      onRetry={onRetry}
      emptyTitle="No users"
      emptyMessage="No users found in the system."
    />
  );
}
