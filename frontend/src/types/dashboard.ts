import type { SeverityLevel, SourceType } from '../utils/constants';

export interface DashboardSummary {
  active_alerts: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
    trend: string;
  };
  crawler_status: {
    active_targets: number;
    queued_jobs: number;
    running_jobs: number;
    pages_today: number;
    success_rate: string;
  };
  actors: {
    total_tracked: number;
    high_risk: number;
    new_today: number;
  };
  recent_alerts: RecentAlert[];
  top_categories: TopCategory[];
}

export interface RecentAlert {
  id: string;
  title: string;
  severity: SeverityLevel;
  created_at: string;
  source_type: SourceType;
}

export interface TopCategory {
  category: string;
  count: number;
  trend: string;
}

export interface TrendingData {
  most_mentioned_products: TrendingProduct[];
  most_active_marketplaces: TrendingMarketplace[];
  top_threat_actors: TrendingActor[];
  language_distribution: LanguageDistribution[];
}

export interface TrendingProduct {
  product: string;
  mentions: number;
  trend: string;
}

export interface TrendingMarketplace {
  site: string;
  posts: number;
  trend: string;
}

export interface TrendingActor {
  pseudonym: string;
  risk_score: number;
  recent_posts: number;
}

export interface LanguageDistribution {
  language: string;
  percentage: number;
}
