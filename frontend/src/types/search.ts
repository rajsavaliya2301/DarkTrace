import type { SourceType } from '../utils/constants';

export interface SearchRequest {
  q: string;
  page?: number;
  per_page?: number;
  source_type?: SourceType;
  category?: string;
  language?: string;
  author?: string;
  date_from?: string;
  date_to?: string;
  has_entities?: string;
  sort_by?: 'relevance' | 'date' | 'score';
  deep_search?: boolean;
}

export interface IndianPIIEntity {
  type: 'aadhaar' | 'pan' | 'voter_id' | 'passport';
  value: string;
}

export interface SearchResult {
  id: string;
  url: string;
  title: string;
  snippet: string;
  author: string;
  source_type: SourceType;
  site_name: string;
  category: string;
  severity_score: number;
  language: string;
  crawled_at: string;
  matched_entities: {
    btc_addresses?: string[];
    emails?: string[];
    indian_ids?: IndianPIIEntity[];
    phone_numbers?: string[];
    indian_addresses?: string[];
  };
  deep_entities?: {
    indian_id_count: number;
    phone_count: number;
    has_aadhaar: boolean;
    has_pan: boolean;
    pii_detected: boolean;
    sample_ids?: string[];
  };
}

export interface SearchFacets {
  categories: FacetItem[];
  source_types: FacetItem[];
  languages: FacetItem[];
}

export interface FacetItem {
  value: string;
  count: number;
}

export interface SearchResponse {
  data: SearchResult[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  facets: SearchFacets;
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: Record<string, string[]>;
  notify_on_new: boolean;
  last_run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSavedSearchRequest {
  name: string;
  query: string;
  filters: Record<string, string[]>;
  notify_on_new: boolean;
}
