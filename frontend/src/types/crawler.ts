import type { SourceType, CrawlFrequency, ParserType, CrawlJobStatus } from '../utils/constants';

export interface CrawlTarget {
  id: string;
  url: string;
  site_name: string;
  source_type: SourceType;
  status: 'active' | 'paused' | 'pending_verification' | 'error';
  crawl_frequency: CrawlFrequency;
  last_crawled: string | null;
  last_status: 'success' | 'failed' | null;
  pages_crawled: number;
  added_by: string;
  added_at: string;
}

export interface AddTargetRequest {
  url: string;
  site_name: string;
  source_type: SourceType;
  crawl_frequency: CrawlFrequency;
  parser_type: ParserType;
  notes?: string;
}

export interface AddTargetResponse {
  id: string;
  url: string;
  status: string;
  created_at: string;
}

export interface TriggerCrawlResponse {
  job_id: string;
  status: string;
  estimated_completion: string;
}

export interface CrawlJob {
  id: string;
  target_id?: string;
  target_url: string;
  status: CrawlJobStatus;
  pages_fetched: number;
  pages_total: number;
  errors: number;
  started_at: string;
  completed_at: string | null;
  proxy_used?: string;
}

export interface CrawlJobsResponse {
  data: CrawlJob[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}
