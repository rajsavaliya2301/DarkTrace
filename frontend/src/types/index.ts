export * from './auth';
export * from './alert';
export * from './crawler';
export * from './watchlist';
export * from './actor';
export * from './report';
export * from './search';
export * from './dashboard';

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
  permissions?: string[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_name: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: string | Record<string, unknown>;
  ip_address: string;
  user_agent: string;
}

export interface SystemHealthResponse {
  status: string;
  services: Record<string, {
    status: string;
    uptime?: string;
    workers?: number;
    queue_depth?: number;
    throughput?: string;
    message?: string;
    health?: string;
    queues?: number;
  }>;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: { field: string; message: string }[];
    request_id: string;
    timestamp: string;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}
