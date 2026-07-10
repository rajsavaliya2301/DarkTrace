import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import UserList from '../components/admin/UserList';
import UserForm from '../components/admin/UserForm';
import AuditLogViewer from '../components/admin/AuditLogViewer';
import SystemHealth from '../components/admin/SystemHealth';
import apiClient from '../api/client';
import type { AdminUser, AuditLogEntry, SystemHealthResponse } from '../types';

type AdminTab = 'users' | 'audit' | 'health';

export default function AdminPage() {
  const [tab, setAdminTab] = useState<AdminTab>('users');
  const [showUserForm, setShowUserForm] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [auditPage, setAuditPage] = useState(1);

  const {
    data: usersData,
    isLoading: usersLoading,
    isError: usersError,
    refetch: refetchUsers,
  } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/users');
      return res.data as { data: AdminUser[] };
    },
  });

  const {
    data: auditData,
    isLoading: auditLoading,
    isError: auditError,
    refetch: refetchAudit,
  } = useQuery({
    queryKey: ['auditLogs', auditPage],
    queryFn: async () => {
      const res = await apiClient.get('/admin/audit-logs', {
        params: { page: auditPage, per_page: 50 },
      });
      return res.data as {
        data: AuditLogEntry[];
        pagination: { page: number; per_page: number; total: number; total_pages: number };
      };
    },
    enabled: tab === 'audit',
  });

  const {
    data: healthData,
    isLoading: healthLoading,
    isError: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: async () => {
      const res = await apiClient.get('/admin/health');
      return res.data as SystemHealthResponse;
    },
    enabled: tab === 'health',
  });

  const handleCreateUser = async (formData: any) => {
    try {
      await apiClient.post('/admin/users', formData);
      setShowUserForm(false);
      refetchUsers();
    } catch {
      // Error handled by interceptor
    }
  };

  const handleUpdateUser = async (formData: any) => {
    if (!editingUser) return;
    try {
      await apiClient.put(`/admin/users/${editingUser.id}`, formData);
      setEditingUser(null);
      refetchUsers();
    } catch {
      // Error handled by interceptor
    }
  };

  const tabs: { key: AdminTab; label: string }[] = [
    { key: 'users', label: 'Users' },
    { key: 'audit', label: 'Audit Logs' },
    { key: 'health', label: 'System Health' },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin"
        subtitle="User management, audit logs, and system configuration"
      />

      <div className="flex gap-1 rounded-lg bg-dark-surface p-1 w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setAdminTab(t.key)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'users' && (
        <>
          <div className="flex justify-end">
            <button
              onClick={() => setShowUserForm(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Add User
            </button>
          </div>
          <UserList
            users={usersData?.data}
            isLoading={usersLoading}
            isError={usersError}
            onRetry={() => refetchUsers()}
            onEdit={(user) => setEditingUser(user)}
          />
        </>
      )}

      {tab === 'audit' && (
        <AuditLogViewer
          logs={auditData?.data}
          isLoading={auditLoading}
          isError={auditError}
          onRetry={() => refetchAudit()}
          page={auditPage}
          totalPages={auditData?.pagination?.total_pages || 1}
          onPageChange={setAuditPage}
        />
      )}

      {tab === 'health' && (
        <SystemHealth
          data={healthData}
          isLoading={healthLoading}
          isError={healthError}
        />
      )}

      {showUserForm && (
        <UserForm
          onSubmit={handleCreateUser}
          onCancel={() => setShowUserForm(false)}
        />
      )}

      {editingUser && (
        <UserForm
          onSubmit={handleUpdateUser}
          onCancel={() => setEditingUser(null)}
          initialData={editingUser}
        />
      )}
    </div>
  );
}
