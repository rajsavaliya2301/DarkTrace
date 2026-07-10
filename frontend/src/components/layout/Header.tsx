import { Menu, Bell, LogOut, User, AlertTriangle, Info, AlertCircle, Skull } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useLogout } from '../../hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import SearchBar from '../common/SearchBar';
import Clock from '../common/Clock';
import ConnectionStatus from '../common/ConnectionStatus';
import { cn } from '../../utils/cn';

interface HeaderProps {
  onMenuToggle: () => void;
}

const severityIcon: Record<string, typeof AlertTriangle> = {
  info: Info,
  low: AlertCircle,
  medium: AlertTriangle,
  high: AlertTriangle,
  critical: Skull,
};

const severityColor: Record<string, string> = {
  info: 'text-gray-400',
  low: 'text-emerald-400',
  medium: 'text-cyan-400',
  high: 'text-amber-400',
  critical: 'text-red-400',
};

export default function Header({ onMenuToggle }: HeaderProps) {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();
  const navigate = useNavigate();
  const location = useLocation();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifPanel, setShowNotifPanel] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  // Fetch recent new alerts for notification bell
  const { data: notifData } = useQuery({
    queryKey: ['notifications', 'recent'],
    queryFn: async () => {
      const res = await apiClient.get('/alerts', { params: { status: 'new', per_page: 5, sort_by: 'created_at', sort_order: 'desc' } });
      return res.data;
    },
    refetchInterval: 30000,
    enabled: !!user,
  });

  const recentAlerts = notifData?.data ?? [];
  const unreadCount = notifData?.pagination?.total ?? 0;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifPanel(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-dark-border bg-dark-surface/80 px-4 backdrop-blur-md">
      <button
        onClick={onMenuToggle}
        className="rounded-lg p-2 text-gray-400 hover:bg-dark-card hover:text-gray-200 lg:hidden"
        aria-label="Toggle menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex-1 max-w-xl">
        <SearchBar />
      </div>

      {/* Live Clock */}
      <Clock />

      {/* Real-time Connection Status */}
      <ConnectionStatus />

      <div className="flex items-center gap-3">
        {/* Notification Bell */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => {
              setShowNotifPanel(!showNotifPanel);
              setShowUserMenu(false);
            }}
            className="relative rounded-lg p-2 text-gray-400 hover:bg-dark-card hover:text-gray-200"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Panel */}
          {showNotifPanel && (
            <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-dark-border bg-dark-card shadow-xl">
              <div className="flex items-center justify-between border-b border-dark-border px-4 py-3">
                <h3 className="text-sm font-semibold text-gray-200">Notifications</h3>
                <button
                  onClick={() => { setShowNotifPanel(false); navigate('/alerts'); }}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  View all
                </button>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {recentAlerts.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-gray-500">
                    No new notifications
                  </div>
                ) : (
                  recentAlerts.slice(0, 5).map((alert: any) => {
                    const SevIcon = severityIcon[alert.severity] || AlertTriangle;
                    return (
                      <button
                        key={alert._id || alert.id}
                        onClick={() => { setShowNotifPanel(false); navigate(`/alerts/${alert._id || alert.id}`); }}
                        className="flex w-full items-start gap-3 border-b border-dark-border px-4 py-3 text-left last:border-0 hover:bg-dark-surface"
                      >
                        <SevIcon className={cn('mt-0.5 h-4 w-4 shrink-0', severityColor[alert.severity] || 'text-gray-400')} />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-200 truncate">{alert.title}</p>
                          <p className="mt-0.5 text-xs text-gray-500 line-clamp-1">{alert.summary || alert.category}</p>
                          <p className="mt-0.5 text-[10px] text-gray-600 capitalize">{alert.severity} · {alert.source_type}</p>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => {
              setShowUserMenu(!showUserMenu);
              setShowNotifPanel(false);
            }}
            className="flex items-center gap-2 rounded-lg p-1.5 text-gray-400 hover:bg-dark-card hover:text-gray-200"
            aria-label="User menu"
            aria-expanded={showUserMenu}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600/20 text-sm font-medium text-blue-400">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="hidden text-sm font-medium text-gray-200 md:block">
              {user?.name || 'User'}
            </span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-dark-border bg-dark-card p-2 shadow-xl">
              <div className="border-b border-dark-border px-3 py-2">
                <p className="text-sm font-medium text-gray-200">{user?.name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <div className="mt-1 space-y-0.5">
                <button
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-400 hover:bg-dark-surface hover:text-gray-200"
                  onClick={() => { setShowUserMenu(false); navigate('/profile'); }}
                >
                  <User className="h-4 w-4" />
                  Profile
                </button>
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    logout.mutate();
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-400 hover:bg-red-500/10"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
