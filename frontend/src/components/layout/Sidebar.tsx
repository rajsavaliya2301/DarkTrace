import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Bell,
  Search,
  Radio,
  ListChecks,
  Users,
  FileText,
  Shield,
  ChevronLeft,
  Skull,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useAuthStore } from '../../store/authStore';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Alerts', path: '/alerts', icon: Bell },
  { label: 'Search', path: '/search', icon: Search },
  { label: 'Crawler', path: '/crawler', icon: Radio },
  { label: 'Watchlists', path: '/watchlists', icon: ListChecks },
  { label: 'Actors', path: '/actors', icon: Users },
  { label: 'Reports', path: '/reports', icon: FileText },
  { label: 'Admin', path: '/admin', icon: Shield },
];

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const user = useAuthStore((s) => s.user);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-full flex-col border-r border-dark-border bg-dark-surface transition-all duration-300 ease-in-out lg:static lg:z-auto',
          isOpen ? 'w-64 translate-x-0' : '-translate-x-full lg:w-16 lg:translate-x-0'
        )}
        aria-label="Sidebar navigation"
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-dark-border px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <Skull className="h-5 w-5 text-white" />
            </div>
            <span
              className={cn(
                'text-lg font-bold text-white transition-opacity duration-200',
                !isOpen && 'lg:hidden'
              )}
            >
              DarkTrace
            </span>
          </div>
          <button
            onClick={onToggle}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-dark-card hover:text-gray-200 lg:block"
            aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <ChevronLeft
              className={cn(
                'h-5 w-5 transition-transform',
                !isOpen && 'lg:rotate-180'
              )}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  onClick={() => {
                    if (window.innerWidth < 1024) onToggle();
                  }}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-blue-600/20 text-blue-400'
                        : 'text-gray-400 hover:bg-dark-card hover:text-gray-200'
                    )
                  }
                  title={!isOpen ? item.label : undefined}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  <span
                    className={cn(
                      'transition-opacity duration-200',
                      !isOpen && 'lg:hidden'
                    )}
                  >
                    {item.label}
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* User info */}
        <div className="border-t border-dark-border p-4">
          <div className={cn('flex items-center gap-3', !isOpen && 'lg:justify-center')}>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600/20 text-sm font-medium text-blue-400">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className={cn('min-w-0', !isOpen && 'lg:hidden')}>
              <p className="truncate text-sm font-medium text-gray-200">
                {user?.name || 'User'}
              </p>
              <p className="truncate text-xs text-gray-500">{user?.role}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
