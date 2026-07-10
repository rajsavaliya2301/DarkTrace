// In development (Vite), the backend serves on /v1 directly.
// In production (nginx), the /api prefix is stripped and /v1 is forwarded.
// Set VITE_API_BASE_URL=/api/v1 in production Docker env.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/v1';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/v1';

export const SEVERITY_LEVELS = ['info', 'low', 'medium', 'high', 'critical'] as const;
export type SeverityLevel = (typeof SEVERITY_LEVELS)[number];

export const SEVERITY_COLORS: Record<SeverityLevel, string> = {
  info: '#6b7280',
  low: '#10b981',
  medium: '#06b6d4',
  high: '#f59e0b',
  critical: '#ef4444',
};

export const SEVERITY_BG_CLASSES: Record<SeverityLevel, string> = {
  info: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  medium: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  high: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export const ALERT_STATUSES = ['new', 'acknowledged', 'investigating', 'resolved', 'false_positive'] as const;
export type AlertStatus = (typeof ALERT_STATUSES)[number];

export const ALERT_CATEGORIES = [
  'ransomware',
  'data_breach',
  'exploit',
  'fraud',
  'illegal_goods',
  'intelligence',
  'malware',
  'services',
] as const;
export type AlertCategory = (typeof ALERT_CATEGORIES)[number];

export const SOURCE_TYPES = ['onion', 'i2p', 'surface'] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

// Must match backend validation pattern in crawler/router.py
export const CRAWL_FREQUENCIES = ['every_1h', 'every_2h', 'every_4h', 'every_6h', 'every_8h', 'every_12h', 'every_24h', 'every_48h', 'every_7d', 'every_30d'] as const;
export type CrawlFrequency = (typeof CRAWL_FREQUENCIES)[number];

export const PARSER_TYPES = ['marketplace', 'forum', 'paste', 'blog', 'general'] as const;
export type ParserType = (typeof PARSER_TYPES)[number];

export const CRAWL_JOB_STATUSES = ['queued', 'in_progress', 'completed', 'failed'] as const;
export type CrawlJobStatus = (typeof CRAWL_JOB_STATUSES)[number];

export const REPORT_TYPES = ['alert_report', 'actor_dossier', 'trend_report', 'raw_export', 'search_results_export'] as const;
export type ReportType = (typeof REPORT_TYPES)[number];

export const REPORT_FORMATS = ['pdf', 'csv', 'json'] as const;
export type ReportFormat = (typeof REPORT_FORMATS)[number];

export const USER_ROLES = ['investigator', 'admin', 'auditor', 'siem_integration'] as const;
export type UserRole = (typeof USER_ROLES)[number];

export const SERVICE_STATUSES = ['up', 'degraded', 'down'] as const;
export type ServiceStatus = (typeof SERVICE_STATUSES)[number];

export const AUDIT_ACTIONS = [
  'login',
  'logout',
  'alert_update',
  'alert_bulk_update',
  'report_generated',
  'report_downloaded',
  'target_added',
  'target_updated',
  'target_deleted',
  'watchlist_created',
  'watchlist_updated',
  'watchlist_deleted',
  'user_created',
  'user_updated',
  'user_deleted',
  'rule_created',
  'rule_updated',
  'rule_deleted',
] as const;
export type AuditAction = (typeof AUDIT_ACTIONS)[number];

export const SEVERITY_ORDER: Record<SeverityLevel, number> = {
  info: 0,
  low: 1,
  medium: 2,
  high: 3,
  critical: 4,
};

export const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', icon: 'LayoutDashboard' },
  { label: 'Alerts', path: '/alerts', icon: 'Bell' },
  { label: 'Search', path: '/search', icon: 'Search' },
  { label: 'Crawler', path: '/crawler', icon: 'Radio' },
  { label: 'Watchlists', path: '/watchlists', icon: 'ListChecks' },
  { label: 'Actors', path: '/actors', icon: 'Users' },
  { label: 'Reports', path: '/reports', icon: 'FileText' },
  { label: 'Admin', path: '/admin', icon: 'Shield' },
] as const;
