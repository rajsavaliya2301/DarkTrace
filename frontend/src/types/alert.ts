import type { SeverityLevel, AlertStatus, AlertCategory, SourceType } from '../utils/constants';

export interface Alert {
  id: string;
  title: string;
  severity: SeverityLevel;
  score: number;
  status: AlertStatus;
  category: AlertCategory;
  source_type: SourceType;
  source_url: string;
  created_at: string;
  acknowledged_by: string | null;
  summary: string;
  matched_keywords: string[];
  actor_pseudonym: string | null;
  actor_profile_id: string | null;
}

export interface AlertsResponse {
  data: Alert[];
  pagination: Pagination;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface AlertDetail {
  id: string;
  title: string;
  severity: SeverityLevel;
  score: number;
  score_breakdown: Record<string, { score: number; weight: number }>;
  status: AlertStatus;
  assignee: string | null;
  category: AlertCategory;
  source: {
    url: string;
    site_name: string;
    source_type: SourceType;
    crawl_timestamp: string;
  };
  content: {
    title: string;
    author: string;
    author_profile_url: string;
    published_date: string;
    content_text: string;
    language: string;
    translated_from: string | null;
  };
  entities: {
    persons: string[];
    organizations: string[];
    btc_addresses: string[];
    emails: string[];
    keywords_matched: string[];
  };
  analysis: {
    sentiment: {
      threat_intent: number;
      hostility: number;
      urgency: number;
    };
    classification: {
      primary: string;
      secondary: string[];
      confidence: number;
    };
  };
  actor: {
    profile_id: string;
    pseudonyms: string[];
    risk_score: number;
    first_seen: string;
    last_seen: string;
    total_posts: number;
    active_marketplaces: string[];
  } | null;
  timeline: TimelineEvent[];
  related_alerts: RelatedAlert[];
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  event: string;
  timestamp: string;
  detail: string;
}

export interface RelatedAlert {
  id: string;
  title: string;
  severity: SeverityLevel;
  created_at: string;
}

export interface AlertUpdateRequest {
  status?: AlertStatus;
  assignee?: string;
  comment?: string;
}

export interface AlertUpdateResponse {
  id: string;
  status: AlertStatus;
  assignee: string | null;
  updated_at: string;
}

export interface BulkAlertRequest {
  alert_ids: string[];
  action: 'acknowledge' | 'investigating' | 'resolved' | 'dismiss';
  assignee?: string;
}

export interface BulkAlertResponse {
  updated_count: number;
  message: string;
}

export interface AlertStats {
  total: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  trend: AlertTrend[];
}

export interface AlertTrend {
  date: string;
  count: number;
  critical: number;
  high: number;
}
