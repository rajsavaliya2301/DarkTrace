import { useAuthStore } from '../store/authStore';
import { User, Shield, Calendar, Mail, Key, Globe } from 'lucide-react';
import PageHeader from '../components/common/PageHeader';
import { usePreferencesStore, REGIONS } from '../store/preferencesStore';

function RegionSelector() {
  const region = usePreferencesStore((s) => s.region);
  const setRegion = usePreferencesStore((s) => s.setRegion);

  return (
    <div className="rounded-xl border border-dark-border bg-dark-card p-6">
      <h3 className="mb-4 text-lg font-semibold text-gray-100">Region & Timezone</h3>
      <p className="mb-4 text-sm text-gray-500">
        Choose your region to see local time in the header. This also helps contextualize threat data.
      </p>

      <div className="relative">
        <Globe className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value as any)}
          className="w-full appearance-none rounded-lg border border-dark-border bg-dark-surface py-2.5 pl-10 pr-10 text-sm text-gray-200 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {REGIONS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.flag} {r.label}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Live preview */}
      <div className="mt-4 flex items-center gap-3 rounded-lg bg-dark-surface px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600/20">
          <span className="text-sm font-bold text-blue-400">
            {(() => {
              try {
                return new Date().toLocaleTimeString('en-US', { timeZone: region, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
              } catch {
                return '--:--:--';
              }
            })()}
          </span>
        </div>
        <div>
          <p className="text-xs text-gray-500">Current time</p>
          <p className="text-sm font-medium text-gray-200">
            {(() => {
              try {
                return new Date().toLocaleDateString('en-US', { timeZone: region, weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
              } catch {
                return '—';
              }
            })()}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Profile"
        subtitle="Your account information and settings"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Avatar & Basic Info */}
        <div className="rounded-xl border border-dark-border bg-dark-card p-6 text-center lg:col-span-1">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-blue-600/20 text-3xl font-bold text-blue-400">
            {user?.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <h2 className="mt-4 text-xl font-semibold text-gray-100">{user?.name}</h2>
          <p className="mt-1 text-sm text-gray-500 capitalize">{user?.role}</p>

          <div className="mt-6 space-y-3 text-left">
            <div className="flex items-center gap-3 rounded-lg bg-dark-surface px-4 py-3">
              <Mail className="h-4 w-4 text-blue-400" />
              <div>
                <p className="text-xs text-gray-500">Email</p>
                <p className="text-sm text-gray-200">{user?.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-dark-surface px-4 py-3">
              <Shield className="h-4 w-4 text-blue-400" />
              <div>
                <p className="text-xs text-gray-500">Role</p>
                <p className="text-sm text-gray-200 capitalize">{user?.role}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-dark-surface px-4 py-3">
              <Key className="h-4 w-4 text-blue-400" />
              <div>
                <p className="text-xs text-gray-500">Permissions</p>
                <p className="text-sm text-gray-200">{user?.permissions?.length || 0} permissions</p>
              </div>
            </div>
          </div>
        </div>

        {/* Account Details & Preferences */}
        <div className="space-y-6 lg:col-span-2">
          {/* Account Details */}
          <div className="rounded-xl border border-dark-border bg-dark-card p-6">
            <h3 className="mb-4 text-lg font-semibold text-gray-100">Account Details</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg bg-dark-surface p-4">
                <p className="text-xs text-gray-500">Name</p>
                <p className="mt-1 text-sm font-medium text-gray-200">{user?.name || '—'}</p>
              </div>
              <div className="rounded-lg bg-dark-surface p-4">
                <p className="text-xs text-gray-500">Email</p>
                <p className="mt-1 text-sm font-medium text-gray-200">{user?.email || '—'}</p>
              </div>
              <div className="rounded-lg bg-dark-surface p-4">
                <p className="text-xs text-gray-500">Role</p>
                <p className="mt-1 text-sm font-medium text-gray-200 capitalize">{user?.role || '—'}</p>
              </div>
              <div className="rounded-lg bg-dark-surface p-4">
                <p className="text-xs text-gray-500">Account Status</p>
                <p className="mt-1 text-sm font-medium text-green-400">Active</p>
              </div>
            </div>
          </div>

          {/* Region / Timezone Preference */}
          <RegionSelector />
        </div>
      </div>
    </div>
  );
}
