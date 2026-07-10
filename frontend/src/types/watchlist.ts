export interface Watchlist {
  id: string;
  name: string;
  description: string;
  keywords: string[];
  regex_patterns: RegexPattern[];
  severity_boost: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  match_count: number;
}

export interface RegexPattern {
  pattern: string;
  label: string;
}

export interface CreateWatchlistRequest {
  name: string;
  description: string;
  keywords: string[];
  regex_patterns?: RegexPattern[];
  severity_boost: number;
  is_active: boolean;
}

export interface UpdateWatchlistRequest {
  keywords?: string[];
  regex_patterns?: RegexPattern[];
  is_active?: boolean;
  severity_boost?: number;
}

export interface CreateWatchlistResponse {
  id: string;
  name: string;
  created_at: string;
}

export interface UpdateWatchlistResponse {
  id: string;
  updated_at: string;
}

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  severity_threshold: number;
  conditions: RuleCondition[];
  notifications: RuleNotification[];
  created_by: string;
  created_at: string;
  triggered_count: number;
}

export interface RuleCondition {
  field: string;
  operator: string;
  value: string[] | string;
}

export interface RuleNotification {
  type: string;
  target?: string;
}

export interface CreateRuleRequest {
  name: string;
  description: string;
  enabled: boolean;
  severity_threshold: number;
  conditions: RuleCondition[];
  notifications: RuleNotification[];
}
